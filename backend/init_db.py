import mysql.connector
from mysql.connector import errorcode

config = {
  'user': 'root',
  'password': 'root', # default password as per requirement, change if needed
  'host': '127.0.0.1',
  'raise_on_warnings': True
}

DB_NAME = 'jingjiabushou'

TABLES = {}
TABLES['stock_list'] = (
    "CREATE TABLE `stock_list` ("
    "  `code` varchar(10) NOT NULL,"
    "  `name` varchar(50) NOT NULL,"
    "  `market` int NOT NULL,"
    "  PRIMARY KEY (`code`)"
    ") ENGINE=InnoDB")

TABLES['call_auction_data'] = (
    "CREATE TABLE `call_auction_data` ("
    "  `id` int NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `time` time NOT NULL,"
    "  `code` varchar(10) NOT NULL,"
    "  `name` varchar(50) NOT NULL,"
    "  `sector` varchar(50) DEFAULT '',"
    "  `price` decimal(10, 2) NOT NULL,"
    "  `bidding_percent` decimal(10, 2) DEFAULT 0.00,"
    "  `bidding_amount` decimal(20, 2) DEFAULT 0.00,"
    "  `asking_amount` decimal(20, 2) DEFAULT 0.00,"
    "  `non_asking_amount` decimal(20, 2) DEFAULT 0.00,"
    "  `non_asking_volume` bigint DEFAULT 0,"
    "  `yidongleixing` varchar(255) DEFAULT '',"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date_time` (`date`, `time`),"
    "  INDEX `idx_date_code` (`date`, `code`),"
    "  INDEX `idx_date_time_code` (`date`, `time`, `code`)"
    ") ENGINE=InnoDB")

TABLES['yesterday_limit_up'] = (
    "CREATE TABLE `yesterday_limit_up` ("
    "  `id` int NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `code` varchar(10) NOT NULL,"
    "  `name` varchar(50) NOT NULL,"
    "  `limit_up_type` varchar(50) NOT NULL,"
    "  `consecutive_days` int DEFAULT 0,"
    "  `edition` int DEFAULT 0,"
    "  `consecutive_boards` int DEFAULT 0,"
    "  `days_boards` varchar(50),"
    "  `limit_up_form` varchar(50),"
    "  `first_limit_up_time` varchar(20),"
    "  `last_limit_up_time` varchar(20),"
    "  `open_count` int DEFAULT 0,"
    "  `expound` text,"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date` (`date`),"
    "  INDEX `idx_date_code` (`date`, `code`)"
    ") ENGINE=InnoDB")

TABLES['core_leaders'] = (
    "CREATE TABLE `core_leaders` ("
    "  `id` int NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `code` varchar(10) NOT NULL,"
    "  `name` varchar(50) NOT NULL,"
    "  `reason` varchar(255),"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date` (`date`)"
    ") ENGINE=InnoDB")

TABLES['sector_sentiment'] = (
    "CREATE TABLE `sector_sentiment` ("
    "  `id` int NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `sector_name` varchar(50) NOT NULL,"
    "  `sentiment_score` int NOT NULL,"
    "  `description` varchar(255),"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date` (`date`)"
    ") ENGINE=InnoDB")

TABLES['index_data'] = (
    "CREATE TABLE `index_data` ("
    "  `id` int NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `time` time NOT NULL,"
    "  `index_code` varchar(20) NOT NULL,"
    "  `index_name` varchar(50) NOT NULL,"
    "  `increase_amount` decimal(10, 2),"
    "  `increase_rate` decimal(10, 2),"
    "  `index_volume` decimal(20, 2),"
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date_time` (`date`, `time`),"
    "  INDEX `idx_index_code` (`index_code`)"
    ") ENGINE=InnoDB")

TABLES['market_sentiment_stats'] = (
    "CREATE TABLE `market_sentiment_stats` ("
    "  `date` date NOT NULL,"
    "  `time` time NOT NULL,"
    "  `limit_up_count` int DEFAULT 0,"
    "  `limit_down_count` int DEFAULT 0,"
    "  `non_st_limit_up_count` int DEFAULT 0,"
    "  `non_st_limit_down_count` int DEFAULT 0,"
    "  `st_limit_up_count` int DEFAULT 0,"
    "  `st_limit_down_count` int DEFAULT 0,"
    "  `rise_count` int DEFAULT 0,"
    "  `fall_count` int DEFAULT 0,"
    "  `flat_count` int DEFAULT 0,"
    "  `market_sentiment` varchar(255),"
    "  `shanghai_turnover` bigint DEFAULT 0,"
    "  `total_turnover` bigint DEFAULT 0,"
    "  `rise_fall_distribution` text,"
    "  `raw_response_json` json,"
    "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
    "  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`date`, `time`)"
    ") ENGINE=InnoDB")

TABLES['market_capacity'] = (
    "CREATE TABLE `market_capacity` ("
    "  `id` bigint NOT NULL AUTO_INCREMENT,"
    "  `date` date NOT NULL,"
    "  `call_auction_amount` int DEFAULT NULL,"
    "  `full_day_amount` int DEFAULT NULL,"
    "  `trends` text,"
    "  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,"
    "  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  INDEX `idx_date` (`date`)"
    ") ENGINE=InnoDB")

def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8mb4'".format(DB_NAME))
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
        exit(1)

def init_db():
    try:
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        try:
            cursor.execute("USE {}".format(DB_NAME))
        except mysql.connector.Error as err:
            print("Database {} does not exist.".format(DB_NAME))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                print("Database {} created successfully.".format(DB_NAME))
                cnx.database = DB_NAME
            else:
                print(err)
                exit(1)

        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                print("Creating table {}: ".format(table_name), end='')
                cursor.execute(table_description)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print("already exists.")
                else:
                    print(err.msg)
            else:
                print("OK")

        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        print("Failed connecting to database: {}".format(err))

if __name__ == "__main__":
    init_db()
