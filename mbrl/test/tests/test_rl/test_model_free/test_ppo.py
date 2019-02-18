from mbrl.envs.gym_env import make
from mbrl.envs.env_spec import EnvSpec
from mbrl.common.sampler.sample_data import TransitionData, TrajectoryData
from mbrl.algo.rl.value_func.mlp_v_value import MLPVValueFunc
from mbrl.algo.rl.policy.normal_distribution_mlp import NormalDistributionMLPPolicy
from mbrl.algo.rl.model_free.ppo import PPO
from mbrl.test.tests.test_setup import TestTensorflowSetup
import tensorflow as tf


class TestPPO(TestTensorflowSetup):
    def test_init(self):
        env = make('Swimmer-v1')
        env_spec = EnvSpec(obs_space=env.observation_space,
                           action_space=env.action_space)

        mlp_v = MLPVValueFunc(env_spec=env_spec,
                              name_scope='mlp_v',
                              mlp_config=[
                                  {
                                      "ACT": "RELU",
                                      "B_INIT_VALUE": 0.0,
                                      "NAME": "1",
                                      "N_UNITS": 16,
                                      "TYPE": "DENSE",
                                      "W_NORMAL_STDDEV": 0.03
                                  },
                                  {
                                      "ACT": "LINEAR",
                                      "B_INIT_VALUE": 0.0,
                                      "NAME": "OUPTUT",
                                      "N_UNITS": 1,
                                      "TYPE": "DENSE",
                                      "W_NORMAL_STDDEV": 0.03
                                  }
                              ])
        policy = NormalDistributionMLPPolicy(env_spec=env_spec,
                                             name_scope='mlp_policy',
                                             mlp_config=[
                                                 {
                                                     "ACT": "RELU",
                                                     "B_INIT_VALUE": 0.0,
                                                     "NAME": "1",
                                                     "N_UNITS": 16,
                                                     "TYPE": "DENSE",
                                                     "W_NORMAL_STDDEV": 0.03
                                                 },
                                                 {
                                                     "ACT": "LINEAR",
                                                     "B_INIT_VALUE": 0.0,
                                                     "NAME": "OUPTUT",
                                                     "N_UNITS": env_spec.flat_action_dim,
                                                     "TYPE": "DENSE",
                                                     "W_NORMAL_STDDEV": 0.03
                                                 }
                                             ],
                                             reuse=False)
        ppo = PPO(
            env_spec=env_spec,
            config_or_config_dict={
                "gamma": 0.995,
                "lam": 0.98,
                "policy_train_iter": 10,
                "value_func_train_iter": 10,
                "clipping_range": None,
                "beta": 1.0,
                "eta": 50,
                "log_var_init": -1.0,
                "kl_target": 0.003,
                "policy_lr": 0.01,
                "value_func_lr": 0.01,
                "value_func_train_batch_size": 10
            },
            value_func=mlp_v,
            stochastic_policy=policy,
            adaptive_learning_rate=True,
            name='ppo',
        )
        ppo.init()
        print(tf.report_uninitialized_variables())
        data = TransitionData(env_spec)
        st = env.reset()
        for i in range(100):
            ac = ppo.predict(st)
            assert ac.shape[0] == 1
            self.assertTrue(env_spec.action_space.contains(ac[0]))
            new_st, re, done, _ = env.step(ac)
            if i == 99:
                done = True
            data.append(state=st, new_state=new_st, action=ac, reward=re, done=done)
        ppo.append_to_memory(data)
        print(ppo.train())

        traj_data = TrajectoryData(env_spec=env_spec)
        traj_data.append(data)
        print(
            ppo.train(trajectory_data=traj_data,
                      train_iter=10,
                      sess=self.sess))
        # ppo.append_to_memory(data)
        # for i in range(1000):
        #     print(ppo.train())


if __name__ == '__main__':
    TestPPO()