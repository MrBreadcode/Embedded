from marshmallow import Schema, fields
from agent.src.schema.accelerometer_schema import AccelerometerSchema
from agent.src.schema.gps_schema import GpsSchema


class AggregatedDataSchema(Schema):
    accelerometer = fields.Nested(AccelerometerSchema)
    gps = fields.Nested(GpsSchema)
    timestamp = fields.DateTime("iso")
    user_id = fields.Int()
