DROP TABLE IF EXISTS "move" CASCADE;

DROP TABLE IF EXISTS game CASCADE;

DROP TABLE IF EXISTS "user" CASCADE;

DROP TYPE IF EXISTS game_status CASCADE;

DROP TYPE IF EXISTS color CASCADE;

CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(25) UNIQUE NOT NULL,
    PASSWORD TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE game_status AS ENUM (
    'white',
    'black',
    'draw',
    'ongoing',
    'aborted'
);

CREATE TYPE color AS ENUM (
    'white',
    'black'
);

CREATE TABLE game (
    id SERIAL PRIMARY KEY,
    player1_id INT NOT NULL,
    player2_id INT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    current_player color,
    game_status game_status NOT NULL,
    CONSTRAINT fk_p1 FOREIGN KEY (player1_id) REFERENCES "user" (id) ON DELETE CASCADE,
    CONSTRAINT fk_p2 FOREIGN KEY (player2_id) REFERENCES "user" (id) ON DELETE CASCADE
);

CREATE TABLE "move" (
    id SERIAL PRIMARY KEY,
    game_id INT NOT NULL,
    move_number INT NOT NULL,
    player_id INT NOT NULL,
    "move" VARCHAR(10) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_game FOREIGN KEY (game_id) REFERENCES game (id) ON DELETE CASCADE,
    CONSTRAINT fk_player FOREIGN KEY (player_id) REFERENCES "user" (id) ON DELETE CASCADE
);

CREATE INDEX idx_game_player1_id ON game (player1_id);

CREATE INDEX idx_game_player2_id ON game (player2_id);

CREATE INDEX idx_move_game_id ON "move" (game_id);

CREATE INDEX idx_move_game_id_move_number ON "move" (game_id, move_number);

