-- Add boss competition columns to member table
ALTER TABLE member ADD COLUMN IF NOT EXISTS boss_comp_pts integer DEFAULT 0;
ALTER TABLE member ADD COLUMN IF NOT EXISTS boss_comp_pts_life integer DEFAULT 0;
ALTER TABLE member ADD COLUMN IF NOT EXISTS boss_comp_wins TEXT[] DEFAULT '{}';

-- Rename skill_comp table to competition
ALTER TABLE skill_comp RENAME TO competition;

-- Add competition_type column to competition table
ALTER TABLE competition ADD COLUMN IF NOT EXISTS competition_type varchar(20) DEFAULT 'skill';

-- Create index on competition_type for faster queries
CREATE INDEX IF NOT EXISTS idx_competition_type ON competition(competition_type);

-- Update existing competitions to have competition_type = 'skill'
UPDATE competition SET competition_type = 'skill' WHERE competition_type IS NULL; 