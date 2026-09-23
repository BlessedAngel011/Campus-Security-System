USE campus_security_db;

-- The mobile application loads these records through GET /api/locations.
-- Alice Campus is campus_id 1 in the mobile registration configuration.

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Main Gate', 'Alice Campus main entrance', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Main Gate'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Great Hall', 'Campus Control and Great Hall area', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Great Hall'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Library', 'Alice Campus library area', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Library'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Student Centre', 'Student Centre area', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Student Centre'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Student Residences', 'Alice Campus residence area', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Student Residences'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Sports Complex', 'Alice Campus sports facilities', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Sports Complex'
);

INSERT INTO locations
    (campus_id, location_name, description, latitude, longitude)
SELECT 1, 'Administration Building', 'Alice Campus administration area', NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM locations
    WHERE campus_id = 1 AND location_name = 'Administration Building'
);

SELECT location_id, campus_id, location_name, description
FROM locations
WHERE campus_id = 1
ORDER BY location_name;
