import sys
#make sure to add the path to the parent directory of the project to the sys.path list. Makes the project modules available for import.
sys.path.append('../')
sys.path.append('../../')
from flask import Flask, request, jsonify
import json
import threading
from persistqueue import Queue
#from erp_integrations.admanager.admanager_create_orderline import create_orderline
import json
import logging
import time
from order_status_db import init_db, get_order_status, insert_order_status, update_order_bad_request
from erp_integration_types.admanager.create_erp_orderline import create_orderline as admanager_create_orderline
from erp_integration_types.au2office.create_erp_orderline import create_orderline as au2office_create_orderline
#from waitress import serve
import os
#from cryptography.fernet import Fernet
#from dotenv import load_dotenv

app = Flask(__name__)

worker_running = threading.Event()

@app.route('/alive', methods=['GET'])
def alive():
    app.logger.info("alive called") 
    return jsonify({"API is alive, worker running": worker_running.is_set()}), 200

@app.route('/check_order_status', methods=['GET'])
def check_order_status():
    order_id = request.args.get('unique_id')
    if not order_id:
        return jsonify({'error': 'order_id is required'}), 400

    status_line = get_order_status(order_id)
    app.logger.info("status_line: " + str(status_line)) 
    if status_line:
        return jsonify({'unique_id': status_line[0], 'status': status_line[1], 'reason': status_line[2]}), 200
    else:
        return jsonify({'error': 'Order not found'}), 404


@app.route('/queue', methods=['GET'])
def queue():
    type = request.args.get('type')
    app.logger.info("queue called") 
    queue_list = []
    if type == 'task':
        queue = task_queue
    elif type == 'error':
        queue = error_queue
    else:
        return jsonify({"error": "Invalid queue type"}), 400
    
    while not queue.empty():
        task = queue.get()
        queue_list.append(task)

    for i in range(len(queue_list)):
        queue.put(queue_list[i])

    queue_data_str = str(queue_list)

    return jsonify({"queue": queue_data_str}), 200

@app.route('/clear_queue', methods=['PUT'])
def clear_queue():
    app.logger.info("clear_queue called") 
    type = request.args.get('type')

    if type == 'task':
        queue = task_queue
    elif type == 'error':
        queue = error_queue
    else:
        return jsonify({"error": "Invalid queue type"}), 400
    
    queue_list = []
    while not queue.empty():
        task = queue.get()
        queue_list.append(task)

    queue_data_str = str(queue_list)
    return jsonify({"Queue elements removed": queue_data_str}), 200

@app.route('/start_worker', methods=['PUT'])
def start_worker():
    app.logger.info("start_worker called")
    worker_running.set()
    return jsonify({"Worker running": worker_running.is_set()}), 200

@app.route('/stop_worker', methods=['PUT'])
def stop_worker():
    app.logger.info("stop_worker called")
    #global worker_running
    worker_running.clear()
    return jsonify({"Worker running": worker_running.is_set()}), 200


@app.route('/create', methods=['POST'])
def create_order():
    app.logger.info("create_order called") 

    json_data = request.get_json()

    data = json.loads(json_data)

    dealer = data['dealer']
    case_nr = data['case_nr']
    product_nr = data['product_nr']
    product_amount = data['product_amount']
    unique_id = data['unique_id']
    username = data['username']
    password = data['password']
    
    insert_order_status(unique_id,'received',json_data)
    
    if not all([dealer, case_nr, product_nr, product_amount, unique_id, username,password]):
        update_order_bad_request(unique_id,json_data)
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Add the task to the queue
    task_queue.put((dealer, case_nr, product_nr, product_amount,unique_id,username,password))

    return jsonify({"message": "Order line creation task added to queue"}), 200


def worker(logger,erp_logger,worker_running,erp_type,task_queue,error_queue,order_status_db):
    while worker_running.wait():
        try:
            dealer, case_nr, product_nr, product_amount, unique_id, username,password = task_queue.get(timeout=1)

            logger.info(f"\n\nIn worker loop: Creating orderline: {dealer}, {case_nr}, {product_nr}, {product_amount}")
        
            try:
                if erp_type == 'admanager':
                    admanager_create_orderline(dealer, case_nr, product_nr, product_amount,unique_id,username,password,logger,order_status_db)
                elif erp_type == 'au2office':
                    au2office_create_orderline(dealer, case_nr, product_nr, product_amount,unique_id,username,password,logger,order_status_db)
                else:
                    erp_logger.error(f"Invalid erp_type: {erp_type}")
                    error_queue.put((dealer, case_nr, product_nr, product_amount,unique_id,username,password,f"Invalid erp_type: {erp_type}"))
                
                task_queue.task_done()
            except Exception as e:
                error_queue.put((dealer, case_nr, product_nr, product_amount,unique_id,username,password,str(e)))
                error_queue.task_done()


        except:
            time.sleep(1)
            continue
    
def create_app(workshop_path,workshop,task_queue,worker_running):
    app.config['workshop'] = workshop
    app.config['task_queue'] = task_queue
    app.config['worker_running'] = worker_running

    file_handler = logging.FileHandler(workshop_path + 'api.log', mode='a')
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    return app


def main(argv):
    api_port =  argv[0] 
    workshop =  argv[1] 
    erp_type =  argv[2]
    api_port_int = int(api_port)
    global task_queue
    global error_queue

    #logger = logging.getLogger(__name__)
    logger = logging.getLogger('waitress')
    

    workshop_path = '../../workshop_logs/'+workshop+'/'
    erp_type_path = 'erp_integration_types/'+erp_type+ '/'
    
    logging.basicConfig(level=logging.INFO,filename=workshop_path + 'create_orderline.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not os.path.exists(workshop_path):
        logging.debug(f"Path {workshop_path} does not exist")
        os.makedirs(workshop_path)

 
    init_db(workshop_path + 'order_status.db')

    sys.path.append(erp_type_path)
    # dynamically import the create_orderline function from the erp integration module that matches a given workshop
    task_queue = Queue(workshop_path + 'task_queue')
    error_queue = Queue(workshop_path + 'error_queue')

    app = create_app(workshop_path,workshop,task_queue,worker_running)

    worker_thread = threading.Thread(target=worker, args=(app.logger,logger,worker_running,erp_type,task_queue,error_queue,workshop_path + 'order_status.db'))
    worker_thread.start()
    serve(app, host='localhost', port=8001)
    #api_thread = threading.Thread(target=serve(app,port=api_port_int))
    #api_thread.start()
    #serve(app,port=api_port_int)

    #app.run(port=api_port_int) # Run the API on the specified port

if __name__ == '__main__':
    main(sys.argv[1:])

