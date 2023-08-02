import boto3
import logging
import json
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return super().default(o)

def _get_service_data(session, region_name, sheet):
    """Get information about a service described on :sheet allocated on a :region_name"""
    log.info("Started: AWS Get Service Data")
    service = sheet["service"]
    function = sheet["function"]

    # optional
    result_key = sheet.get("result_key", None)
    parameters = sheet.get("parameters", None)

    log.info(
        "Getting data on service %s with function %s in region %s",
        service,
        function,
        region_name,
    )

    response = ""

    try:
        # session = boto3.Session(profile_name=profile_name)
        client = session.client(service, region_name=region_name)

        if parameters is not None:
            if result_key:
                response = client.__getattribute__(function)(**parameters).get(
                    result_key
                )
            else:
                response = client.__getattribute__(function)(**parameters)
        elif result_key:
            response = client.__getattribute__(function)().get(result_key)
        else:
            response = client.__getattribute__(function)()
            # Remove ResponseMetadata as it's not useful
            response.pop("ResponseMetadata", None)
    except Exception as exception:
        log.error("Error while processing %s, %s.\n%s", service, region_name, exception)

    log.debug("Result:{{%s}}", response)

    log.info("Finished: AWS Get Service Data")

    return response


def main(services_sheet, output_file):
    session = boto3.Session()

    with open(services_sheet, 'r') as f:
        services = json.load(f)

    regions = [region['RegionName'] for region in session.client('ec2').describe_regions()['Regions']]

    results = []

    for region in regions:
        for service in services:
            result = _get_service_data(session, region, service)
            if result:
                results.append({
                    'region': region,
                    'service': service['service'],
                    'result': result
                })

    with open(output_file, 'w') as f:
        json.dump(results, f, cls=DateTimeEncoder)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='List all resources in all AWS services and regions.')
    parser.add_argument('services_sheet', type=str, help='Path to the services sheet JSON file')
    parser.add_argument('output_file', type=str, help='Path to the output JSON file')
    args = parser.parse_args()
    main(args.services_sheet, args.output_file)
