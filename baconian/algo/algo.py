from baconian.core.core import Basic, EnvSpec
from baconian.core.status import StatusWithSubInfo
import abc
from typeguard import typechecked
from baconian.common.logging import Recorder
from baconian.core.parameters import Parameters


class Algo(Basic):
    """
    Abstract class for algorithms
    """
    STATUS_LIST = ['NOT_INIT', 'JUST_INITED', 'TRAIN', 'TEST']
    INIT_STATUS = 'NOT_INIT'

    @typechecked
    def __init__(self, env_spec: EnvSpec, name: str = 'algo'):
        """
        Constructor

        :param env_spec: environment specifications
        :type env_spec: EnvSpec
        :param name: name of the algorithm
        :type name: str
        """

        super().__init__(status=StatusWithSubInfo(obj=self), name=name)
        self.env_spec = env_spec
        self.parameters = Parameters(dict())
        self.recorder = Recorder(default_obj=self)

    def init(self):
        """
        Initialization method, such as network random initialization in Tensorflow

        :return:
        """
        self._status.set_status('JUST_INITED')

    def train(self, *arg, **kwargs) -> dict:
        """
        Training API, specific arguments should be defined by each algorithms itself.

        :return: training results, e.g., loss
        :rtype: dict
        """

        self._status.set_status('TRAIN')
        return dict()

    def test(self, *arg, **kwargs) -> dict:
        """
        Testing API, most of the evaluation can be done by agent instead of algorithms, so this API can be skipped

        :return: test results, e.g., rewards
        :rtype: dict
        """

        self._status.set_status('TEST')
        return dict()

    @abc.abstractmethod
    def predict(self, *arg, **kwargs):
        """
        Predict function, given the obs as input, return the action, obs will be read as the first argument passed into
        this API, like algo.predict(obs=x, ...)

        :return: predicted action
        :rtype: np.ndarray
        """
        raise NotImplementedError

    @abc.abstractmethod
    def append_to_memory(self, *args, **kwargs):
        """
        For off-policy algorithm, use this API to append the data into replay buffer. samples will be read as the first
        argument passed into this API, like algo.append_to_memory(samples=x, ...)

        """
        raise NotImplementedError

    @property
    def is_training(self):
        """
        A boolean indicate the if the algorithm is in training status

        :return: True if in training
        :rtype: bool
        """
        return self.get_status()['status'] == 'TRAIN'

    @property
    def is_testing(self):
        """
        A boolean indicate the if the algorithm is in training status

        :return: True if in testing
        :rtype: bool
        """
        return self.get_status()['status'] == 'TEST'

#
# class AlgoPolicyWrapper(Algo):
#     def __init__(self, policy: Policy, env_spec: EnvSpec, name: str = 'algo'):
#         super().__init__(env_spec, name)
#         self.policy = policy
#
#     def init(self):
#         super().init()
#
#     def train(self, *arg, **kwargs) -> dict:
#         return super().train(*arg, **kwargs)
#
#     def test(self, *arg, **kwargs) -> dict:
#         return super().test(*arg, **kwargs)
#
#     def predict(self, obs, **kwargs):
#         self.policy.forward(obs=obs)
#
#     def append_to_memory(self, *args, **kwargs):
#         pass
#
#     @property
#     def is_training(self):
#         return super().is_training()
#
#     @property
#     def is_testing(self):
#         return super().is_testing()