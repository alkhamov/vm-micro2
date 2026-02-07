CREATE TABLE IF NOT EXISTS requests (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  action TEXT NOT NULL,
  use_case TEXT
);

INSERT INTO requests (name, action)
VALUES
  ('subscriber1', 'add'),
  ('subscription', 'delete'),
  ('subscriber2', 'add');
