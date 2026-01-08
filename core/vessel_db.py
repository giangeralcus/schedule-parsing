"""
Vessel Database with Dual-Mode Support (Docker + Cloud + Offline)
=================================================================
Auto-learning vessel name correction from OCR errors
Supports: Supabase Cloud, Supabase Docker (local), Offline fallback
"""

import os
import json
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from datetime import datetime

from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import dependencies
HAS_POSTGREST = False
HAS_FUZZY = False

try:
    from postgrest import SyncPostgrestClient
    HAS_POSTGREST = True
except ImportError:
    pass

try:
    from rapidfuzz import fuzz, process
    HAS_FUZZY = True
except ImportError:
    try:
        from thefuzz import fuzz, process
        HAS_FUZZY = True
    except ImportError:
        pass


class VesselDatabase:
    """
    Vessel name matcher with dual Supabase support (Cloud + Docker)

    Priority:
    1. Docker local (localhost:54321) - if available
    2. Supabase Cloud - if Docker not available
    3. Offline fallback - if no connection

    Features:
    - Auto-detect Docker vs Cloud
    - Sync between Docker and Cloud
    - Auto-learn OCR variations
    """

    # Default configurations
    DOCKER_URL = "http://localhost:8000"
    DOCKER_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJhbm9uIiwKICAgICJpc3MiOiAic3VwYWJhc2UtZGVtbyIsCiAgICAiaWF0IjogMTY0MTc2OTIwMCwKICAgICJleHAiOiAxNzk5NTM1NjAwCn0.dc_X5iR_VP_qT0zsiyj_I_OZ2T9FtRU2BBNWN8Bu4GE"

    LOCAL_CACHE_FILE = Path(__file__).parent.parent / "data" / "vessels_cache.json"

    def __init__(self,
                 cloud_url: str = None,
                 cloud_key: str = None,
                 docker_url: str = None,
                 docker_key: str = None,
                 fuzzy_threshold: int = 80,
                 prefer_docker: bool = True):
        """
        Initialize vessel database with dual-mode support

        Args:
            cloud_url: Supabase Cloud URL
            cloud_key: Supabase Cloud anon key
            docker_url: Docker Supabase URL (default: localhost:54321)
            docker_key: Docker Supabase anon key
            fuzzy_threshold: Minimum similarity score (0-100)
            prefer_docker: If True, prefer Docker over Cloud when both available
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.prefer_docker = prefer_docker

        # Connection clients
        self.docker_client = None
        self.cloud_client = None
        self.active_client = None
        self.active_mode = "offline"

        # In-memory cache
        self._vessels: Dict[str, str] = {}      # {id: name}
        self._aliases: Dict[str, str] = {}      # {alias_upper: vessel_name}
        self._vessel_ids: Dict[str, str] = {}   # {name: id}

        # Configuration
        self.cloud_url = cloud_url or os.getenv("SUPABASE_URL")
        self.cloud_key = cloud_key or os.getenv("SUPABASE_ANON_KEY")
        self.docker_url = docker_url or os.getenv("SUPABASE_DOCKER_URL", self.DOCKER_URL)
        self.docker_key = docker_key or os.getenv("SUPABASE_DOCKER_KEY", self.DOCKER_ANON_KEY)

        # Initialize connections
        self._init_connections()

    def _init_connections(self):
        """Initialize and test connections"""
        if not HAS_POSTGREST:
            logger.warning("postgrest not installed, using offline mode")
            self._load_fallback_data()
            return

        # Try Docker first (if preferred)
        if self.prefer_docker:
            if self._try_docker():
                return
            if self._try_cloud():
                return
        else:
            if self._try_cloud():
                return
            if self._try_docker():
                return

        # Fallback to offline
        logger.warning("No database connection, using offline mode")
        self._load_fallback_data()

    def _try_docker(self) -> bool:
        """Try to connect to Docker Supabase"""
        try:
            rest_url = f"{self.docker_url}/rest/v1"
            headers = {
                "apikey": self.docker_key,
                "Authorization": f"Bearer {self.docker_key}"
            }
            client = SyncPostgrestClient(rest_url, headers=headers)

            # Test connection
            result = client.from_("vessels").select("id").limit(1).execute()

            self.docker_client = client
            self.active_client = client
            self.active_mode = "docker"
            self._load_from_database()
            logger.info("Connected to Docker (localhost)")
            return True
        except Exception as e:
            logger.debug(f"Docker not available: {e}")
            return False

    def _try_cloud(self) -> bool:
        """Try to connect to Supabase Cloud"""
        if not self.cloud_url or not self.cloud_key:
            return False

        try:
            rest_url = f"{self.cloud_url}/rest/v1"
            headers = {
                "apikey": self.cloud_key,
                "Authorization": f"Bearer {self.cloud_key}"
            }
            client = SyncPostgrestClient(rest_url, headers=headers)

            # Test connection
            result = client.from_("vessels").select("id").limit(1).execute()

            self.cloud_client = client
            self.active_client = client
            self.active_mode = "cloud"
            self._load_from_database()
            logger.info("Connected to Supabase Cloud")
            return True
        except Exception as e:
            logger.debug(f"Cloud not available: {e}")
            return False

    def _load_from_database(self):
        """Load vessels and aliases from active database"""
        try:
            # Load vessels
            result = self.active_client.from_("vessels").select("id, name").eq("is_active", "true").execute()
            for v in result.data:
                self._vessels[v["id"]] = v["name"]
                self._vessel_ids[v["name"]] = v["id"]

            # Load aliases
            result = self.active_client.from_("vessel_aliases").select("alias, vessel_id").execute()
            for a in result.data:
                vessel_name = self._vessels.get(a["vessel_id"])
                if vessel_name:
                    self._aliases[a["alias"].upper()] = vessel_name

            logger.info(f"Loaded {len(self._vessels)} vessels, {len(self._aliases)} aliases from {self.active_mode}")

            # Save to local cache for offline use
            self._save_local_cache()
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
            self._load_fallback_data()

    def _load_fallback_data(self):
        """Load from local cache or hardcoded fallback"""
        # Try local cache first
        if self._load_local_cache():
            return

        # Hardcoded fallback
        fallback_vessels = {
            "DANUM 175": ["DANUM175", "OANUM 175", "DANUM I75"],
            "CNC JUPITER": ["CNCJUPITER", "CNC JUPTER"],
            "SPIL NISAKA": ["SPILNISAKA"],
            "JULIUS-S.": ["JULIUS S", "JULIUS-S", "JULTUS"],
            "SKY PEACE": ["SKYPEACE"],
            "MARTIN SCHULTE": ["MARTINSCHULTE"],
            "COSCO ISTANBUL": ["COSCOISTANBUL"],
            "EVER GOLDEN": ["EVERGOLDEN"],
            "ONE HARMONY": ["ONEHARMONY"],
            "HAMBURG EXPRESS": ["HAMBURGEXPRESS"],
        }

        for name, aliases in fallback_vessels.items():
            fake_id = name.lower().replace(" ", "_").replace(".", "").replace("-", "_")
            self._vessels[fake_id] = name
            self._vessel_ids[name] = fake_id
            self._aliases[name.upper()] = name
            for alias in aliases:
                self._aliases[alias.upper()] = name

        self.active_mode = "offline"
        logger.info(f"Loaded {len(self._vessels)} vessels from fallback data (offline mode)")

    def _save_local_cache(self):
        """Save current data to local JSON cache"""
        try:
            self.LOCAL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                "vessels": self._vessels,
                "aliases": self._aliases,
                "vessel_ids": self._vessel_ids,
                "updated_at": datetime.now().isoformat(),
                "source": self.active_mode
            }
            with open(self.LOCAL_CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)

            # Security: Set restrictive file permissions (owner read/write only)
            # On Windows this has limited effect but doesn't cause errors
            try:
                import stat
                os.chmod(self.LOCAL_CACHE_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
            except (OSError, AttributeError):
                pass  # Ignore on Windows or if chmod fails
        except Exception as e:
            logger.error(f"Failed to save local cache: {e}")

    def _load_local_cache(self) -> bool:
        """Load from local JSON cache"""
        try:
            if self.LOCAL_CACHE_FILE.exists():
                with open(self.LOCAL_CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                self._vessels = cache_data.get("vessels", {})
                self._aliases = cache_data.get("aliases", {})
                self._vessel_ids = cache_data.get("vessel_ids", {})
                self.active_mode = "cache"
                logger.info(f"Loaded {len(self._vessels)} vessels from local cache")
                return True
        except Exception as e:
            logger.error(f"Failed to load local cache: {e}")
        return False

    def match(self, ocr_text: str) -> Tuple[str, int, str]:
        """
        Match OCR text to vessel name

        Returns:
            Tuple of (vessel_name, confidence, match_type)
        """
        if not ocr_text:
            return ("", 0, "none")

        ocr_clean = ocr_text.strip().upper()

        # Step 1: Exact match in aliases
        if ocr_clean in self._aliases:
            return (self._aliases[ocr_clean], 100, "exact")

        # Step 2: Fuzzy match
        if HAS_FUZZY and self._vessels:
            vessel_names = list(self._vessels.values())
            result = process.extractOne(
                ocr_clean,
                vessel_names,
                scorer=fuzz.token_sort_ratio
            )

            if result and result[1] >= self.fuzzy_threshold:
                matched_name = result[0]
                confidence = result[1]

                # Auto-learn: save new alias
                self._save_alias(ocr_clean, matched_name)

                return (matched_name, confidence, "fuzzy")

        # No match
        return (ocr_text.strip(), 0, "none")

    def _save_alias(self, alias: str, vessel_name: str):
        """Save new alias to database and local cache"""
        # Update local cache immediately
        self._aliases[alias.upper()] = vessel_name

        # Save to active database
        if self.active_client and vessel_name in self._vessel_ids:
            vessel_id = self._vessel_ids[vessel_name]
            try:
                self.active_client.from_("vessel_aliases").insert({
                    "vessel_id": vessel_id,
                    "alias": alias,
                    "source": "ocr_auto",
                    "confidence": 90
                }).execute()
                logger.info(f"Auto-learned: '{alias}' -> '{vessel_name}' ({self.active_mode})")

                # Update local cache file
                self._save_local_cache()
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    logger.error(f"Failed to save alias: {e}")

    def add_vessel(self, name: str, carrier: str = None, aliases: List[str] = None) -> bool:
        """Add new vessel to database"""
        if self.active_client:
            try:
                result = self.active_client.from_("vessels").insert({
                    "name": name,
                    "carrier": carrier
                }).execute()

                vessel_id = result.data[0]["id"]
                self._vessels[vessel_id] = name
                self._vessel_ids[name] = vessel_id
                self._aliases[name.upper()] = name

                if aliases:
                    for alias in aliases:
                        self._save_alias(alias.upper(), name)

                self._save_local_cache()
                logger.info(f"Added vessel: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to add vessel: {e}")
                return False
        else:
            # Offline mode
            fake_id = name.lower().replace(" ", "_")
            self._vessels[fake_id] = name
            self._vessel_ids[name] = fake_id
            self._aliases[name.upper()] = name
            if aliases:
                for alias in aliases:
                    self._aliases[alias.upper()] = name
            self._save_local_cache()
            return True

    def sync(self, direction: str = "cloud_to_docker") -> Dict:
        """
        Sync data between Cloud and Docker

        Args:
            direction: "cloud_to_docker" or "docker_to_cloud"

        Returns:
            Sync statistics
        """
        stats = {"vessels_synced": 0, "aliases_synced": 0, "errors": []}

        # Ensure both connections
        if not self.docker_client:
            self._try_docker()
        if not self.cloud_client:
            self._try_cloud()

        if not self.docker_client or not self.cloud_client:
            stats["errors"].append("Both Docker and Cloud connections required for sync")
            return stats

        try:
            if direction == "cloud_to_docker":
                source, target = self.cloud_client, self.docker_client
            else:
                source, target = self.docker_client, self.cloud_client

            # Get source vessels
            source_vessels = source.from_("vessels").select("*").execute().data

            # Sync vessels
            for vessel in source_vessels:
                try:
                    target.from_("vessels").upsert({
                        "name": vessel["name"],
                        "carrier": vessel.get("carrier"),
                        "is_active": vessel.get("is_active", True)
                    }, on_conflict="name").execute()
                    stats["vessels_synced"] += 1
                except Exception as e:
                    stats["errors"].append(f"Vessel {vessel['name']}: {e}")

            # Get target vessel IDs for alias mapping
            target_vessels = target.from_("vessels").select("id, name").execute().data
            target_vessel_map = {v["name"]: v["id"] for v in target_vessels}

            # Get source aliases
            source_aliases = source.from_("vessel_aliases").select("*, vessels(name)").execute().data

            # Sync aliases
            for alias in source_aliases:
                vessel_name = alias.get("vessels", {}).get("name")
                if vessel_name and vessel_name in target_vessel_map:
                    try:
                        target.from_("vessel_aliases").upsert({
                            "vessel_id": target_vessel_map[vessel_name],
                            "alias": alias["alias"],
                            "source": alias.get("source", "sync"),
                            "confidence": alias.get("confidence", 100)
                        }, on_conflict="alias").execute()
                        stats["aliases_synced"] += 1
                    except Exception as e:
                        stats["errors"].append(f"Alias {alias['alias']}: {e}")

            logger.info(f"Sync complete: {stats['vessels_synced']} vessels, {stats['aliases_synced']} aliases")

            # Reload from active database
            self._load_from_database()

        except Exception as e:
            stats["errors"].append(str(e))

        return stats

    def switch_mode(self, mode: str) -> bool:
        """
        Switch between docker/cloud/offline mode

        Args:
            mode: "docker", "cloud", or "offline"
        """
        if mode == "docker":
            return self._try_docker()
        elif mode == "cloud":
            return self._try_cloud()
        elif mode == "offline":
            self.active_client = None
            self.active_mode = "offline"
            self._load_fallback_data()
            return True
        return False

    def get_all_vessels(self) -> List[str]:
        """Get list of all vessel names"""
        return list(self._vessels.values())

    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            "total_vessels": len(self._vessels),
            "total_aliases": len(self._aliases),
            "mode": self.active_mode,
            "docker_connected": self.docker_client is not None,
            "cloud_connected": self.cloud_client is not None,
            "fuzzy_available": HAS_FUZZY,
            "fuzzy_threshold": self.fuzzy_threshold
        }

    def reload(self):
        """Reload data from active database"""
        if self.active_client:
            self._vessels.clear()
            self._aliases.clear()
            self._vessel_ids.clear()
            self._load_from_database()
        else:
            self._load_fallback_data()


# Singleton instance
_db_instance: Optional[VesselDatabase] = None


def get_vessel_db() -> VesselDatabase:
    """Get or create singleton vessel database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = VesselDatabase()
    return _db_instance


def match_vessel(ocr_text: str) -> str:
    """
    Convenience function to match vessel name

    Args:
        ocr_text: Raw OCR text

    Returns:
        Corrected vessel name
    """
    db = get_vessel_db()
    name, confidence, match_type = db.match(ocr_text)
    return name
