
-- Add vehicle types to the sighting and bike tables

ALTER TABLE sighting ADD vehicle_type TEXT;
ALTER TABLE bike ADD vehicle_type TEXT;

UPDATE sighting set vehicle_type = "bike";
UPDATE bike set vehicle_type = "bike";

