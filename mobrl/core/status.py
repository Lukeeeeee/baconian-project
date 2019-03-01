import abc

import typeguard as tg
from typeguard import typechecked
from copy import deepcopy
from mobrl.common.util.logging import ConsoleLogger


class Status(object):

    def __init__(self, obj):
        self.obj = obj
        self._status_val = None
        if hasattr(obj, 'STATUS_LIST'):
            self._status_list = obj.STATUS_LIST
        else:
            self._status_list = None
        if hasattr(obj, 'INIT_STATUS') and obj.INIT_STATUS is not None:
            self.set_status(new_status=obj.INIT_STATUS)
        else:
            self._status_val = None

    def __call__(self, *args, **kwargs):
        return dict(status=self._status_val)

    @tg.typechecked
    def set_status(self, new_status: str):
        if self._status_list:
            try:
                assert new_status in self._status_list
            except AssertionError as e:
                print("{} New status :{} not in the status list: {} ".format(e, new_status, self._status_list))
            self._status_val = new_status
        else:
            self._status_val = new_status

    def get_status(self) -> dict:
        return self()


class StatusWithInfo(Status):
    @abc.abstractmethod
    def append_new_info(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def has_info(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def update_info(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def reset(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_specific_info_key_status(self, info_key, *args, **kwargs):
        raise NotImplementedError


class StatusWithSingleInfo(StatusWithInfo):
    # todo StatusWithInfo
    def __init__(self, obj):
        super().__init__(obj)

        self._info_dict = {}

    def __call__(self, *args, **kwargs):
        res = super().__call__(*args, **kwargs)
        return {**res, **self._info_dict}

    def set_status(self, new_status: str):
        return super().set_status(new_status)

    @typechecked
    def get_status(self) -> dict:
        return self()

    def append_new_info(self, info_key: str, init_value, under_status=None):
        if info_key == 'status':
            raise ValueError("can use key: status which is a system default key")
        if info_key in self._info_dict:
            return
        else:
            self._info_dict[info_key] = init_value

    def get_specific_info_key_status(self, info_key, *args, **kwargs):
        try:
            return self._info_dict[info_key]
        except KeyError:
            ConsoleLogger().print('ERROR',
                                  'try to access info key status: {} of obj: {}'.format(info_key, self.obj.name))
            return None

    def has_info(self, info_key, **kwargs):
        return info_key in self._info_dict

    def update_info(self, info_key, increment, under_status=None):
        if not self.has_info(info_key=info_key):
            self.append_new_info(info_key=info_key, init_value=0)
        self._info_dict[info_key] += increment

    def reset(self):
        self._info_dict = {}


class StatusWithSubInfo(StatusWithInfo):

    def __init__(self, obj):
        super().__init__(obj)
        if not hasattr(obj, 'STATUS_LIST') or not hasattr(obj, 'INIT_STATUS'):
            raise ValueError(
                "StatusWithSubInfo require the source object to have class attr: STATUS_LIST and INIT_STATUS")

        self._info_dict_with_sub_info = {}
        for key in self._status_list:
            self._info_dict_with_sub_info[key] = {}

    def __call__(self, *args, **kwargs):
        res = super().__call__(*args, **kwargs)
        return {**res, **self._info_dict_with_sub_info[self._status_val]}

    def set_status(self, new_status: str):
        return super().set_status(new_status)

    def get_status(self) -> dict:
        return self()

    def get_specific_info_key_status(self, info_key, under_status, *args, **kwargs):
        try:
            return self._info_dict_with_sub_info[under_status][info_key]
        except KeyError:
            ConsoleLogger().print('ERROR', 'try to access info key status: {} under status {} of obj: {}'.
                                  format(info_key, under_status, self.obj.name))
            return None

    def append_new_info(self, info_key: str, init_value, under_status=None):
        if not under_status:
            under_status = self._status_val
        if info_key == 'status':
            raise ValueError("can use key: status which is a system default key")
        if info_key in self._info_dict_with_sub_info[under_status]:
            return
        else:
            self._info_dict_with_sub_info[under_status][info_key] = init_value

    def has_info(self, info_key, under_status=None):
        if not under_status:
            under_status = self._status_val
        return info_key in self._info_dict_with_sub_info[under_status]

    def update_info(self, info_key, increment, under_status=None):
        if not under_status:
            under_status = self._status_val
        if not self.has_info(info_key=info_key, under_status=under_status):
            self.append_new_info(info_key=info_key, init_value=0, under_status=under_status)
        self._info_dict_with_sub_info[under_status][info_key] += increment

    def reset(self):
        for key in self._status_list:
            self._info_dict_with_sub_info[key] = {}


class StatusCollector(object):

    def __init__(self):
        self._register_status_dict = []

    def __call__(self, *args, **kwargs):
        stat_dict = dict()
        for val in self._register_status_dict:
            obj = val['obj']
            assert hasattr(obj, '_status')
            assert isinstance(getattr(obj, '_status'), StatusWithInfo)
            assert getattr(obj, '_status').has_info(info_key=val['info_key'], under_status=val['under_status'])

            res = obj._status.get_specific_info_key_status(under_status=val['under_status'],
                                                           info_key=val['info_key'])
            stat_dict[val['return_name']] = deepcopy(res)
        return stat_dict

    def get_status(self) -> dict:
        return self()

    def register_info_key_status(self, obj, info_key: str, return_name: str, under_status=None):
        for val in self._register_status_dict:
            assert return_name != val['return_name']
        self._register_status_dict.append(
            dict(obj=obj, info_key=info_key, under_status=under_status, return_name=return_name))


def register_counter_info_to_status_decorator(increment, info_key, under_status: (str, tuple) = None,
                                              ignore_wrong_status=False):
    def wrap(fn):
        if under_status:
            assert isinstance(under_status, (str, tuple))
            if isinstance(under_status, str):
                final_st = tuple([under_status])
            else:
                final_st = under_status

        else:
            final_st = (None,)

        def wrap_with_self(self, *args, **kwargs):
            # todo call the fn first in order to get a correct status
            # todo a bug here, which is record() called in fn will lost the just appended info_key at the very first
            obj = self
            if not hasattr(obj, '_status') or not isinstance(getattr(obj, '_status'), StatusWithInfo):
                raise ValueError(
                    ' the object {} does not not have attribute StatusWithInfo instance or hold wrong type of Status'.format(
                        obj))

            assert isinstance(getattr(obj, '_status'), StatusWithInfo)
            obj_status = getattr(obj, '_status')
            for st in final_st:
                obj_status.append_new_info(info_key=info_key, init_value=0, under_status=st)
            res = fn(self, *args, **kwargs)
            for st in final_st:
                if st and st != obj.get_status()['status'] and not ignore_wrong_status:
                    raise ValueError('register counter info under status: {} but got status {}'.format(st,
                                                                                                       obj.get_status()[
                                                                                                           'status']))
            obj_status.update_info(info_key=info_key, increment=increment,
                                   under_status=obj.get_status()['status'])
            return res

        return wrap_with_self

    return wrap


_global_experiment_status = StatusWithSingleInfo(obj=None)

from mobrl.config.global_config import GlobalConfig

for key in GlobalConfig.DEFAULT_EXPERIMENT_END_POINT.keys():
    _global_experiment_status.append_new_info(info_key=key, init_value=0)


def get_global_experiment_status() -> StatusWithSingleInfo:
    # todo how to use global status
    return globals()['_global_experiment_status']


def reset_global_experiment_status():
    globals()['_global_experiment_status'].reset()