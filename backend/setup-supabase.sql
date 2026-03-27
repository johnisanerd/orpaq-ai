-- Run this in Supabase SQL Editor

-- Businesses table
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    website TEXT,
    phone TEXT,
    email TEXT,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    address TEXT,
    rating FLOAT,
    reviews_count INTEGER,
    source TEXT DEFAULT 'google_maps',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Website analyses table
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    screenshot_url TEXT,
    pagespeed_score INTEGER,
    pagespeed_issues JSONB,
    mobile_friendly BOOLEAN,
    ai_ui_score FLOAT,
    ai_outdated BOOLEAN,
    ai_issues JSONB,
    analysis_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    lead_score INTEGER NOT NULL,
    priority TEXT DEFAULT 'low',
    outreach_message TEXT,
    redesign_suggestions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for now)
CREATE POLICY "Enable all for anon" ON businesses FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all for anon" ON analyses FOR ALL TO anon USING (true) WITH CHECK (true);
CREATE POLICY "Enable all for anon" ON leads FOR ALL TO anon USING (true) WITH CHECK (true);
