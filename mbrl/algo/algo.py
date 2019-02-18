from mbrl.core.basic import Basic
import abc
from mbrl.envs.env_spec import EnvSpec
from typeguard import typechecked
from mbrl.common.util.logger import Logger


# import numpy as np


class Algo(Basic, abc.ABC):
    STATUS_LIST = ['NOT_INIT', 'JUST_INITED', 'TRAIN', 'TEST']
    INIT_STATUS = 'NOT_INIT'

    @typechecked
    def __init__(self, env_spec: EnvSpec, name: str = 'algo'):
        self.env_spec = env_spec
        self._name = name
        super().__init__()

    @property
    def name(self):
        return self._name

    def init(self):
        self.status.set_status('JUST_INITED')

    def train(self, *arg, **kwargs) -> dict:
        self.status.set_status('TRAIN')
        return dict()

    def test(self, *arg, **kwargs) -> dict:
        self.status.set_status('TEST')
        return dict()

    def predict(self, *arg, **kwargs):
        raise NotImplementedError

    def append_to_memory(self, *args, **kwargs):
        raise NotImplementedError

    def register_logger(self, logger: Logger):
        raise NotImplementedError