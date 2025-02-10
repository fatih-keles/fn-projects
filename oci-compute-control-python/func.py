#
# oci-compute-control-python version 1.0.
#
# Copyright (c) 2020 Oracle, Inc.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#

import io
import json
from typing import Any
import oci
import logging
import subprocess
import platform
import socket

from fdk import response

def instance_status(compute_client, instance_id):
    return compute_client.get_instance(instance_id).data.lifecycle_state

def instance_start(compute_client, instance_id):
    print('Starting Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'STOPPED':
            try:
                resp = compute_client.instance_action(instance_id, 'START')
                print('Start response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Starting instance failed. {0}' .format(e))
                raise
        else:
            print('The instance was in the incorrect state to start' .format(instance_id))
            raise
    except oci.exceptions.ServiceError as e:
        print('Starting instance failed. {0}'.format(e))
        raise
    print('Started Instance: {}'.format(instance_id))
    return instance_status(compute_client, instance_id)

def instance_stop(compute_client, instance_id):
    print('Stopping Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'RUNNING':
            try:
                resp = compute_client.instance_action(instance_id, 'STOP')
                print('Stop response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Stopping instance failed. {0}' .format(e))
                raise
        else:
            print('The instance was in the incorrect state to stop' .format(instance_id))
            raise
    except oci.exceptions.ServiceError as e:
        print('Stopping instance failed. {0}'.format(e))
        raise
    print('Stopped Instance: {}'.format(instance_id))
    return instance_status(compute_client, instance_id)

# reset instance
def instance_reset(compute_client: Any, instance_ocid: str) -> str:
    """
    Reset an instance
    """
    try:
        resp = compute_client.instance_action(instance_ocid, 'RESET')
        logging.getLogger().info("Reset response code: {0}".format(resp.status))
    except oci.exceptions.ServiceError as e:
        logging.getLogger().error("Resetting instance failed. {0}".format(e))
        raise
    return compute_client.get_instance(instance_ocid).data.lifecycle_state

# set log level
def set_log_level(config: Any) -> None:
    """
    Set logging level, Default is ERROR
    """
    s_log_level = config["log-level"]
    log_level = logging.ERROR
    if s_log_level == "ERROR":
        log_level = logging.ERROR
    if s_log_level == "INFO":
        log_level = logging.INFO
    if s_log_level == "DEBUG":
        log_level = logging.DEBUG
    logging.getLogger().setLevel(log_level)
    # logging.getLogger('oci').setLevel(logging.DEBUG)

# ping an IP address to check if it is reachable
def ping(ip: str, debug: bool = False) -> bool:
    """Ping an IP address and return True if reachable, False otherwise."""
    # Determine the ping command based on the OS
    param = "-n 1" if platform.system().lower() == "windows" else "-c 1"
    command = ["ping", param, ip]
    
    if debug:
        logging.getLogger().debug(f"DEBUG: Running command: {' '.join(command)}")

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if debug:
            logging.getLogger().debug(f"DEBUG: Output:\n{result.stdout}")
            logging.getLogger().debug(f"DEBUG: Errors:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        logging.getLogger().error(f"ERROR: Exception occurred: {e}")
        return False

# List of common ports to test
COMMON_PORTS = {
    22: "SSH",
    53: "DNS",
    80: "HTTP",
    123: "NTP",
    125: "SMTP",
    135: "RPC (Remote Procedure Call)",
    443: "HTTPS",
    445: "SMB (File Sharing)",
    1433: "Microsoft SQL Server",
    5985: "WinRM (Windows Remote Management)",
    5986: "WinRM over HTTPS",
    3389: "RDP (Windows Remote Desktop)",
    3306: "MySQL",
    5432: "PostgreSQL",
    6379: "Redis"
}

def is_port_open(host: str, port: int, timeout: int = 3) -> bool:
    """Check if a specific port is open on a host."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def scan_common_ports(host: str, debug: bool = False) -> bool:
    """Scan a host for common open ports."""
    open_ports = []
    for port, service in COMMON_PORTS.items():
        if is_port_open(host, port):
            open_ports.append(f"{port} ({service})")
            logging.getLogger().debug(f"✅ {host} is reachable on: {port} ({service})")
            if not debug:
                return True

    if open_ports:
        logging.getLogger().debug(f"✅ {host} is reachable on: {', '.join(open_ports)}")
    else:
        logging.getLogger().debug(f"❌ No common ports are open on {host}")

    return len(open_ports) > 0


# FN entry point
def handler(ctx, data: io.BytesIO=None):
    """ 
    Get fn context config
    can ve set by DevOps teams
    """
    config = ctx.Config()
    set_log_level(config)
    
    # check if any paraneters passed during invocation 
    instance_ocid = None
    instance_ip = None
    try:
        body = json.loads(data.getvalue())
        instance_ocid = body.get("instance-ocid")
        instance_ip = body.get("instance-ip")
    except (Exception) as ex:
        # check if any paraneters passed by context 
        instance_ocid = config["instance-ocid"]
        instance_ip = config["instance-ip"]
        
        if instance_ocid == None:
            err_text = "instance-ocid and instance-ip need to be passed to the function, either by invocation or context"
            logging.getLogger().error("Error : {}".format(err_text))
            err_text = str(ex)
            logging.getLogger().error("Error : {}".format(err_text))
            raise
    
    # get instance principals 
    signer = oci.auth.signers.get_resource_principals_signer()
    logging.getLogger().debug("signer : {}".format(signer))
    
    # check if the instance is reachable
    # is_reachable = ping(instance_ip, logging.getLogger().getEffectiveLevel() == logging.DEBUG)
    is_reachable = scan_common_ports(instance_ip, logging.getLogger().getEffectiveLevel() == logging.DEBUG)
    if is_reachable:
        logging.getLogger().info(f"Ping to {instance_ip}: Success")
        logging.getLogger().info(f"<CAPTURE> Ping Successfull, Instance {instance_ip} is reachable</CAPTURE>")
        return response.Response(
            ctx, 
            response_data=json.dumps({"status": "{0}".format("Success"),"message": "Ping Successfull, Instance is reachable"}),
            headers={"Content-Type": "application/json"}
        )
    
    # instance is unreachable, check the status
    # restart the instance 
    logging.getLogger().info(f"Ping to {instance_ip} failed, will restart the instance")    
    compute_client = oci.core.ComputeClient(config={}, signer=signer)
    instance_state = instance_reset(compute_client, instance_ocid)
    
    logging.getLogger().info(f"Instance was unreachable, instance state after reset is {instance_state}")
    logging.getLogger().info(f"<CAPTURE> Ping failed Instance {instance_ip} is unreachable, instance state after reset is {instance_state} </CAPTURE>")
    return response.Response(
        ctx, 
        response_data=json.dumps({"status": "{0}".format("Success"),"message": "Instance was unreachable, instance state after reset is {0}".format(instance_state)}),
        headers={"Content-Type": "application/json"}
    )

# Local test 
if __name__ == "__main__":
    # test_ip = "8.8.8.8"  # Google's public DNS
    # test_ip = "139.185.35.245"  # Google's public DNS
    # is_reachable = ping(test_ip)
    # print(f"Ping to {test_ip}: {'Success' if is_reachable else 'Failed'}")
    
    # config = oci.config.from_file(file_location="~/.oci/config", profile_name="A2B")
    
    
    # Example usage
    test_ip = "139.185.35.245"  # Replace with the actual IP you want to test
    test_ip = "193.123.77.119"  # Replace with the actual IP you want to test
    scan_common_ports(test_ip)