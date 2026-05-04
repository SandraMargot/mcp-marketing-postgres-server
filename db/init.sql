-- Read-only role
CREATE ROLE mcp_readonly;
GRANT CONNECT ON DATABASE marketing TO mcp_readonly;

CREATE TABLE campaigns (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    channel     VARCHAR(50)  NOT NULL,  -- email / social / paid_search / display
    start_date  DATE         NOT NULL,
    end_date    DATE,
    budget_usd  NUMERIC(10,2) NOT NULL,
    status      VARCHAR(20)  NOT NULL   -- active / completed / paused
);

CREATE TABLE daily_metrics (
    id           SERIAL PRIMARY KEY,
    campaign_id  INTEGER REFERENCES campaigns(id),
    date         DATE    NOT NULL,
    impressions  INTEGER NOT NULL,
    clicks       INTEGER NOT NULL,
    conversions  INTEGER NOT NULL,
    spend_usd    NUMERIC(10,2) NOT NULL
);

GRANT SELECT ON campaigns, daily_metrics TO mcp_readonly;
GRANT mcp_readonly TO analyst;

-- Synthetic data — 6 campaigns
INSERT INTO campaigns (name, channel, start_date, end_date, budget_usd, status) VALUES
('Spring Email Blast',     'email',       '2024-03-01', '2024-03-31', 12000.00, 'completed'),
('Q1 Paid Search',         'paid_search', '2024-01-15', '2024-03-15', 45000.00, 'completed'),
('Social Awareness Apr',   'social',      '2024-04-01', '2024-04-30', 8500.00,  'completed'),
('Display Retargeting',    'display',     '2024-04-10', NULL,          5000.00,  'active'),
('Summer Paid Search',     'paid_search', '2024-06-01', NULL,         38000.00,  'active'),
('Newsletter June',        'email',       '2024-06-01', '2024-06-30',  3200.00,  'paused');

-- Daily metrics (90 days, realistic variance per channel)
INSERT INTO daily_metrics (campaign_id, date, impressions, clicks, conversions, spend_usd)
SELECT
    c.id,
    d::date,
    CASE c.channel
        WHEN 'paid_search' THEN (800  + random()*400)::int
        WHEN 'email'       THEN (5000 + random()*2000)::int
        WHEN 'social'      THEN (3000 + random()*1500)::int
        WHEN 'display'     THEN (8000 + random()*3000)::int
    END AS impressions,
    CASE c.channel
        WHEN 'paid_search' THEN (60   + random()*40)::int
        WHEN 'email'       THEN (200  + random()*100)::int
        WHEN 'social'      THEN (90   + random()*60)::int
        WHEN 'display'     THEN (40   + random()*30)::int
    END AS clicks,
    CASE c.channel
        WHEN 'paid_search' THEN (8  + random()*6)::int
        WHEN 'email'       THEN (15 + random()*10)::int
        WHEN 'social'      THEN (5  + random()*4)::int
        WHEN 'display'     THEN (2  + random()*2)::int
    END AS conversions,
    ROUND((c.budget_usd / 90 * (0.85 + random()*0.30))::numeric, 2)
FROM campaigns c
CROSS JOIN generate_series(c.start_date, COALESCE(c.end_date, CURRENT_DATE), '1 day') d
WHERE d::date <= CURRENT_DATE;