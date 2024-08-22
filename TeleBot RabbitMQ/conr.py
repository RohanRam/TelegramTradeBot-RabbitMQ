import pika
import json

RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_QUEUE = 'telebot'

def callback(ch, method, properties, body):
    message = json.loads(body)
    stock = message.get('stock')
    quantity = message.get('quantity')

    print(f"PURCHASE INFORMATION: Stock = {stock}, Quantity = {quantity}")
    
def main():
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
    channel = connection.channel() 
    channel.queue_declare(queue=RABBITMQ_QUEUE)
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=True)

    print('\t\n\t TRADE INFORMATION \n')
    channel.start_consuming()

if __name__ == '__main__':
    main()
