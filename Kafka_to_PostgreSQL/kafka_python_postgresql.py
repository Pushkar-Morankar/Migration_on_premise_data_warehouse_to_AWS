from confluent_kafka import Consumer, KafkaException
import psycopg2
from psycopg2 import Error
import json
from configfiles import kafka_server_config, postgresql_config

def insert_into_postgresql(cursor, conn, data):
    # Inserting a single Kafka message (dictionary) into PostgreSQL tables.
    try:
        # Insert into customers
        cursor.execute("""
            INSERT INTO customers (customer_id, customer_name, segment, country, city, state, postal_code, region) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON CONFLICT DO NOTHING
        """, (
            data["Customer ID"], data["Customer Name"], data["Segment"], 
            data["Country"], data["City"], data["State"], data["Postal Code"], data["Region"]
        ))

        # Insert into products
        cursor.execute("""
            INSERT INTO products (product_id, product_name, category, sub_category) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT DO NOTHING
        """, (
            data["Product ID"], data["Product Name"], data["Category"], data["Sub-Category"]
        ))

        # Insert into orders 
        cursor.execute("""
            INSERT INTO orders (order_id, order_date, ship_date, ship_mode, customer_id, product_id, sales) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id, product_id, customer_id) 
            DO UPDATE SET 
                sales = orders.sales + EXCLUDED.sales
        """, (
            data["Order ID"], data["Order Date"], data["Ship Date"], data["Ship Mode"], 
            data["Customer ID"], data["Product ID"], data["Sales"]
        ))

        # Commit the transaction
        conn.commit()
    except Exception as e:
        print(f"Error inserting data into PostgreSQL: {e}")
        conn.rollback()  # Roll back on error
        raise  # Raise the exception for manual handling

def main():
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(**postgresql_config)
        cursor = conn.cursor()
        print("Connected to PostgreSQL database.")
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return

    # Kafka Consumer Setup
    props = kafka_server_config.copy() 
    props["group.id"] = "python-group-2"
    props["auto.offset.reset"] = "earliest"
    
    try:
        consumer = Consumer(props)
        consumer.subscribe(["topic_01"])
        print("Kafka consumer subscribed to topic_01.")

        record_id = 1
        while True:
            event = consumer.poll(1.0)
            if event is None:
                continue
            if event.error():
                raise KafkaException(event.error())
            
            val = event.value().decode('utf-8')
            partition = event.partition()
            print(f'Received: {val} from partition {partition}')
            
            # Deserialize the JSON string into a dictionary
            data = json.loads(val)
            print(f"Parsed data: {data}")
            
            # Insert received data into PostgreSQL
            insert_into_postgresql(cursor, conn, data)
            record_id += 1

    except KafkaException as e:
        print(f"Kafka error: {e}")
    except KeyboardInterrupt:
        print("User canceled the consumer.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        consumer.close()
        cursor.close()
        conn.close()
        print("Closed Kafka consumer and PostgreSQL connection.")

if __name__ == '__main__':
    main()