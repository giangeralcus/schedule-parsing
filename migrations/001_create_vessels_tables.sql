-- Migration: Create vessels and vessel_aliases tables for fuzzy matching
-- Project: Schedule Parser v3.0
-- Date: 2026-01-07

-- ============================================
-- Table: vessels (Master data)
-- ============================================
CREATE TABLE IF NOT EXISTS public.vessels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    carrier VARCHAR(50),                    -- CMA-CGM, MAERSK, OOCL, etc
    imo_number VARCHAR(20),                 -- IMO vessel number (optional)
    call_sign VARCHAR(20),                  -- Radio call sign (optional)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lookup
CREATE INDEX IF NOT EXISTS idx_vessels_name ON public.vessels(name);
CREATE INDEX IF NOT EXISTS idx_vessels_carrier ON public.vessels(carrier);

-- ============================================
-- Table: vessel_aliases (OCR variations)
-- ============================================
CREATE TABLE IF NOT EXISTS public.vessel_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vessel_id UUID NOT NULL REFERENCES public.vessels(id) ON DELETE CASCADE,
    alias VARCHAR(100) NOT NULL UNIQUE,
    source VARCHAR(50) DEFAULT 'manual',    -- 'manual', 'ocr_auto', 'import'
    confidence INTEGER DEFAULT 100,          -- 0-100, how confident this alias is correct
    match_count INTEGER DEFAULT 0,           -- How many times this alias was matched
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);

-- Index for fast alias lookup
CREATE INDEX IF NOT EXISTS idx_vessel_aliases_alias ON public.vessel_aliases(alias);
CREATE INDEX IF NOT EXISTS idx_vessel_aliases_vessel_id ON public.vessel_aliases(vessel_id);

-- ============================================
-- Enable RLS (Row Level Security)
-- ============================================
ALTER TABLE public.vessels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vessel_aliases ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for authenticated users
CREATE POLICY "Allow all for authenticated" ON public.vessels
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated" ON public.vessel_aliases
    FOR ALL USING (true);

-- ============================================
-- Function: Update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for vessels
DROP TRIGGER IF EXISTS update_vessels_updated_at ON public.vessels;
CREATE TRIGGER update_vessels_updated_at
    BEFORE UPDATE ON public.vessels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Function: Increment match count on alias use
-- ============================================
CREATE OR REPLACE FUNCTION increment_alias_match()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.vessel_aliases
    SET match_count = match_count + 1,
        last_used_at = now()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Initial seed data
-- ============================================
INSERT INTO public.vessels (name, carrier) VALUES
    ('DANUM 175', 'CMA-CGM'),
    ('CNC JUPITER', 'CMA-CGM'),
    ('SPIL NISAKA', 'MAERSK'),
    ('JULIUS-S.', 'MAERSK'),
    ('SKY PEACE', 'MAERSK'),
    ('MARTIN SCHULTE', 'MAERSK'),
    ('COSCO ISTANBUL', 'OOCL'),
    ('EVER GOLDEN', 'EVERGREEN'),
    ('ONE HARMONY', 'ONE'),
    ('HAMBURG EXPRESS', 'HAPAG-LLOYD')
ON CONFLICT (name) DO NOTHING;

-- Insert aliases for each vessel
INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT v.id, v.name, 'manual' FROM public.vessels v
ON CONFLICT (alias) DO NOTHING;

-- Common OCR variations
INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'DANUM175', 'manual' FROM public.vessels WHERE name = 'DANUM 175'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'OANUM 175', 'ocr_auto' FROM public.vessels WHERE name = 'DANUM 175'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'DANUM I75', 'ocr_auto' FROM public.vessels WHERE name = 'DANUM 175'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'CNCJUPITER', 'manual' FROM public.vessels WHERE name = 'CNC JUPITER'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'CNC JUPTER', 'ocr_auto' FROM public.vessels WHERE name = 'CNC JUPITER'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'SPILNISAKA', 'manual' FROM public.vessels WHERE name = 'SPIL NISAKA'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'COSCOISTANBUL', 'manual' FROM public.vessels WHERE name = 'COSCO ISTANBUL'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'JULIUS S', 'manual' FROM public.vessels WHERE name = 'JULIUS-S.'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'JULIUS-S', 'manual' FROM public.vessels WHERE name = 'JULIUS-S.'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'SKYPEACE', 'manual' FROM public.vessels WHERE name = 'SKY PEACE'
ON CONFLICT (alias) DO NOTHING;

INSERT INTO public.vessel_aliases (vessel_id, alias, source)
SELECT id, 'MARTINSCHULTE', 'manual' FROM public.vessels WHERE name = 'MARTIN SCHULTE'
ON CONFLICT (alias) DO NOTHING;

-- ============================================
-- Verify data
-- ============================================
-- SELECT v.name, COUNT(a.id) as alias_count
-- FROM vessels v
-- LEFT JOIN vessel_aliases a ON v.id = a.vessel_id
-- GROUP BY v.name;
