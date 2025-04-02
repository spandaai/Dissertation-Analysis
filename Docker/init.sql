USE da;

CREATE TABLE IF NOT EXISTS Feedbacks (
   id INT AUTO_INCREMENT PRIMARY KEY,
   selected_text TEXT,
   feedback TEXT,
   pre_analysis TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    degree VARCHAR(255) NOT NULL,
    topic TEXT NOT NULL,
    total_score INT,
    evaluator VARCHAR(255),
    CONSTRAINT unique_user UNIQUE (name, degree, topic(255))
);

CREATE TABLE IF NOT EXISTS UserScores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    dimension_name VARCHAR(255),
    score INT,
    data TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);