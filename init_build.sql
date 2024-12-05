USE feedbackDb;

CREATE TABLE IF NOT EXISTS Feedbacks (
   id INT AUTO_INCREMENT PRIMARY KEY,
   selected_text TEXT,
   feedback TEXT,
   pre_analysis TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);