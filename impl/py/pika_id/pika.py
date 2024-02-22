import base64
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, TypeVar
from pika_id.snowflake import EpochResolvable, Snowflake
import uuid

P = TypeVar('P', bound=str)

@dataclass
class PikaPrefixDefinition(Generic[P]):
    prefix: P
    description: str = field(default="")
    secure: bool = field(default=False)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<PikaPrefixDefinition prefix={self.prefix} description={self.description} secure={self.secure} metadata={self.metadata}>"


@dataclass
class DecodedPika(Generic[P]):
    prefix: P
    tail: str
    snowflake: int
    node_id: int
    seq: int
    prefix_record: PikaPrefixDefinition[P]
    version: int = field(default=1)

    def __repr__(self) -> str:
        return f"<DecodedPika prefix={self.prefix} tail={self.tail} snowflake={self.snowflake} node_id={self.node_id} seq={self.seq} version={self.version} prefix_record={self.prefix_record}>"


class InvalidPrefixError(TypeError):
    def __init__(self, prefix: str):
        super().__init__(f"Invalid prefix: {prefix}")


class Pika(Generic[P]):
    """
    Pika is a unique ID generator that generates IDs. Pika is a port 
    of the original Pika library, written in TypeScript. Pika takes a 
    list of prefixes and generates IDs based on the prefixes. An example 
    for calling the class is as follows:
    
    ```py
    from pika import Pika, PikaPrefixDefinition

    prefixes = [
        PikaPrefixDefinition(prefix="u", description="User ID"),
        PikaPrefixDefinition(prefix="g", description="Group ID"),
        PikaPrefixDefinition(prefix="c", description="Channel ID"),
    ]

    pika = Pika(prefixes)
    ```

    Pika also supports a few options, which can be passed in. 
    The options are as follows:

    - `epoch`: The epoch to use for the Snowflake generator. Defaults to 1640995200000.
    - `node_id`: The node ID to use for the Snowflake generator. Defaults to 0.
    - `suppress_prefix_warnings`: Whether to suppress warnings when an unregistered prefix is used. Defaults to False.

    ```py
    from pika import Pika, PikaPrefixDefinition, PikaInitializationOptions

    prefixes = [
        PikaPrefixDefinition(prefix="u", description="User ID"),
        PikaPrefixDefinition(prefix="g", description="Group ID"),
        PikaPrefixDefinition(prefix="c", description="Channel ID"),
    ]

    pika = Pika(prefixes, epoch=1640995200000, node_id=0, suppress_prefix_warnings=False)
    ```
    """
    prefixes: Dict[str, PikaPrefixDefinition[P]]
    snowflake: Snowflake
    suppress_prefix_warnings: bool

    def __init__(
        self, 
        prefixes: List['PikaPrefixDefinition[P]'], 
        epoch: EpochResolvable = 1640995200000, 
        node_id: int = 0, 
        suppress_prefix_warnings: bool = False, 
    ):
        self.snowflake = Snowflake(epoch, node_id)
        self.suppress_prefix_warnings = suppress_prefix_warnings
        self.prefixes = { prefix.prefix : prefix for prefix in prefixes }

    def validate(self, maybe_id: str, expect_prefix: P = None) -> bool:
        parts = maybe_id.split('_')
        tail = parts[-1]
        prefix = '_'.join(parts[:-1])
        
        if not tail:
            return False
        
        if expect_prefix and prefix != expect_prefix:
            return False
        
        if expect_prefix:
            return prefix == expect_prefix
        
        print(prefix, self.prefixes)

        return prefix in self.prefixes

    def gen(self, prefix: P) -> str:
        """
        Generates a Pika ID with the given prefix. If the prefix is not registered, a warning will be printed.

        Args:
            prefix (P): The prefix to use for the ID.

        Returns:
            str: The generated ID.

        Examples:
            ```py
            from pika import Pika, PikaPrefixDefinition

            prefixes = [
                PikaPrefixDefinition(prefix="u", description="User ID"),
                PikaPrefixDefinition(prefix="g", description="Group ID"),
                PikaPrefixDefinition(prefix="c", description="Channel ID"),
            ]

            pika = Pika(prefixes)

            user_id = pika.gen("u")
            ```
        """

        if prefix not in self.prefixes and not self.suppress_prefix_warnings:
            print(f"Warning: Unregistered prefix ({prefix}) was used.")
        
        snowflake = self.snowflake.gen()  # Assuming Snowflake has a gen() method
        
        prefix_definition = self.prefixes.get(prefix)
        secure_prefix = f"s_{uuid.uuid4().hex}_" if prefix_definition and prefix_definition.secure else ''
        
        tail = base64.urlsafe_b64encode(f"{secure_prefix}{snowflake}".encode()).decode()
        return f"{prefix.lower()}_{tail}"

    def decode(self, id: str) -> DecodedPika[P]:
        """
        Decodes a Pika ID into a DecodedPika object.

        Args:
            id (str): The ID to decode.

        Returns:
            DecodedPika[P]: The decoded Pika ID.

        Raises:
            ValueError: If the ID is invalid.

        Examples:
            ```py
            from pika import Pika, PikaPrefixDefinition

            prefixes = [
                PikaPrefixDefinition(prefix="u", description="User ID"),
                PikaPrefixDefinition(prefix="g", description="Group ID"),
                PikaPrefixDefinition(prefix="c", description="Channel ID"),
            ]

            pika = Pika(prefixes)

            decoded = pika.decode("u_1_1_1")

            print(decoded)
            ```
        """
        try:
            parts = id.split('_')
            tail = parts[-1]
            prefix: P = '_'.join(parts[:-1])

            decoded_tail = base64.urlsafe_b64decode(tail).decode()
            sf = decoded_tail.split('_').pop()
            if not sf:
                raise ValueError('Attempted to decode invalid pika; tail was corrupt')

            deconstructed_snowflake = self.snowflake.deconstruct(sf)
            
            return DecodedPika(
                prefix=prefix,
                tail=tail,
                snowflake=deconstructed_snowflake.id,
                node_id=deconstructed_snowflake.node_id,
                seq=deconstructed_snowflake.seq,
                prefix_record=self.prefixes[prefix]
            )
        except Exception as e:
            print(f"Error: Failed to decode ID {id}. {str(e)}")
            raise e

    def compute_node_id(self) -> int:
        # This method gets the Node ID from machine's MAC address
        # Implementing this requires using third-party libraries in Python, e.g., `uuid` or `socket`
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
        return int(mac.replace(":", ""), 16) % 1024