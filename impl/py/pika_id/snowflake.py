from datetime import datetime
from typing import Optional, Union

EpochResolvable = Union[int, datetime]

class DeconstructedSnowflake:
    id: int
    timestamp: int
    node_id: int
    seq: int
    epoch: int

class Snowflake:
    epoch: int
    node_id: int
    seq: int = 0
    last_sequence_exhaustion: int = 0

    def __init__(self, epoch: EpochResolvable, node_id: Union[int, int]) -> None:
        self.epoch = self._normalize_epoch(epoch)
        self.node_id = node_id

    def gen(self, timestamp: Optional[EpochResolvable] = None) -> str:
        n_timestamp = self._normalize_epoch(timestamp or datetime.now())

        if self.seq == 4095 and n_timestamp == self.last_sequence_exhaustion:
            # purposely blocking
            while (datetime.now().timestamp() * 1000) - n_timestamp < 1:
                pass

        self.seq = 0 if self.seq >= 4095 else self.seq + 1
        if self.seq == 4095:
            self.last_sequence_exhaustion = int(datetime.now().timestamp() * 1000)

        return str(((n_timestamp - self.epoch) << 22) | ((self.node_id & 0b1111111111) << 12) | self.seq)

    def deconstruct(self, id: Union[str, int]) -> DeconstructedSnowflake:
        big_int = int(id)

        return DeconstructedSnowflake(
            id=big_int,
            timestamp=(big_int >> 22) + self.epoch,
            node_id=(big_int >> 12) & 0b1111111111,
            seq=big_int & 0b111111111111,
            epoch=self.epoch,
        )

    def _normalize_epoch(self, epoch: EpochResolvable) -> int:
        return int(epoch.timestamp() * 1000) if isinstance(epoch, datetime) else epoch