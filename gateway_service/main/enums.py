from enum import Enum, unique


@unique
class BaseEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(name: str, *_):
        """
        Automatically generate values for enum.
        Enum values are lower-cased enum member names.
        """
        return name.lower()

    @classmethod
    def get_values(cls) -> list[str]:
        # noinspection PyUnresolvedReferences
        return [m.value for m in cls]


class RabbitStatus(BaseEnum):
    CONNECTING = "Connecting to the RabbitMQ..."
    CONNECTED = "Successfully connected to the RabbitMQ!"
    NOT_CONNECTED = "The message could not be sent because the connection with RabbitMQ is not established"


class RabbitMessageType(BaseEnum):
    FILE_UPLOADED = "File Uploaded"
