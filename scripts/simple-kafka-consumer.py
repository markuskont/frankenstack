#!/usr/bin/env python3

# A simple python script for consuming kafka messages according to user-defined command line arguments
# Mainly for testing and reference when implementing custom consumers

import argparse
import json
from kafka import KafkaConsumer

def positiveInt(value):
    ivalue = int(value)
    if ivalue <= 0:
         raise argparse.ArgumentTypeError("should be > 0, is %s " % value)
    return ivalue

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--brokers",
            dest="brokers",
            nargs = "+",
            default=["localhost:9092"],
            help="Kafka broker. Multiple can be defained separated by whitespace. Note that this option is only used for bootstrapping, so a single broker in cluster is enough.")

    parser.add_argument("--group-id",
            dest="groupid",
            default=None,
            help="Optional group id for committing offsets."
            )

    parser.add_argument("--no-consume",
            dest="noConsume",
            action="store_true",
            default=False,
            help="Only connect to brokers without consuming any messages. Useful for printing debug information.")

    parser.add_argument("--consume-topics",
            dest="topics",
            nargs = "+",
            default=None,
            help="Kafka topics to consume. Multiple can be defained separated by whitespace.")

    parser.add_argument("--beginning",
            dest="beginning",
            action="store_true",
            default=False,
            help="Consume messages from first available messages in topic. By default, tail from end.")

    parser.add_argument("--no-commit-offsets",
            dest="disableOffsetCommit",
            action="store_true",
            default=False,
            help="Disable offset commit. Consumed message offsets would not be stored under consumer group. Defaults to false."
            )
    parser.add_argument("--timeout",
            dest="timeout",
            type=positiveInt,
            default=300,
            help="Automatically close consumer if no events are observed in N seconds. Defaults to 300")

    args = parser.parse_args()

    offset = "earliest" if args.beginning else "latest"
    commit = False if args.disableOffsetCommit else True
    consumer = KafkaConsumer(
            bootstrap_servers=args.brokers,
            group_id=args.groupid,
            auto_offset_reset=offset,
            enable_auto_commit=commit,
            consumer_timeout_ms=args.timeout*1000)

    data = {}
    data["topics"] = consumer.topics()

    data["partitions"] = {}
    for topic in data["topics"]:
        data["partitions"][topic] = consumer.partitions_for_topic(topic)

    if not args.noConsume:
        consumer.subscribe(args.topics)
        data["consumed"] = 0
        try:
            for msg in consumer:
                d = json.loads(msg.value.decode("utf-8"))
                d["kafka"] = {}
                d["kafka"]["timestamp"] = msg.timestamp
                d["kafka"]["partition"] = msg.partition
                d["kafka"]["offset"] = msg.offset
                d["kafka"]["key"] = msg.key.decode("utf-8") if msg.key else None
                print(json.dumps(d))
                data["consumed"] += 1
        except KeyboardInterrupt as e:
                consumer.close(autocommit=False)

    print(data) if args.noConsume else print("Consumed:", data["consumed"], "messages")
