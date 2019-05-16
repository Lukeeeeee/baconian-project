"""
A simple example to show how to build up an experiment with Dyna training and testing on Pendulum-v0
"""
from baconian.core.core import EnvSpec
from baconian.envs.gym_env import make
from baconian.algo.rl.value_func.mlp_q_value import MLPQValueFunction
from baconian.algo.rl.model_free.ddpg import DDPG
from baconian.algo.rl.policy.deterministic_mlp import DeterministicMLPPolicy
from baconian.core.agent import Agent
from baconian.algo.rl.misc.epsilon_greedy import EpsilonGreedy
from baconian.core.experiment import Experiment
from baconian.config.global_config import GlobalConfig
from baconian.core.status import get_global_status_collect
from baconian.common.schedules import PeriodicalEventSchedule
from baconian.algo.dynamics.mlp_dynamics_model import ContinuousMLPGlobalDynamicsModel
from baconian.algo.rl.model_based.dyna import Dyna
from baconian.algo.dynamics.reward_func.reward_func import RandomRewardFunc
from baconian.algo.dynamics.terminal_func.terminal_func import FixedEpisodeLengthTerminalFunc
from baconian.core.flow.dyna_flow import DynaFlow, create_dyna_flow


def task_fn():
    env = make('Pendulum-v0')
    name = 'demo_exp'
    env_spec = EnvSpec(obs_space=env.observation_space,
                       action_space=env.action_space)

    mlp_q = MLPQValueFunction(env_spec=env_spec,
                              name_scope=name + '_mlp_q',
                              name=name + '_mlp_q',
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
    policy = DeterministicMLPPolicy(env_spec=env_spec,
                                    name_scope=name + '_mlp_policy',
                                    name=name + '_mlp_policy',
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

    ddpg = DDPG(
        env_spec=env_spec,
        config_or_config_dict={
            "REPLAY_BUFFER_SIZE": 10000,
            "GAMMA": 0.999,
            "Q_NET_L1_NORM_SCALE": 0.01,
            "Q_NET_L2_NORM_SCALE": 0.01,
            "CRITIC_LEARNING_RATE": 0.001,
            "ACTOR_LEARNING_RATE": 0.001,
            "DECAY": 0.5,
            "BATCH_SIZE": 50,
            "TRAIN_ITERATION": 1,
            "critic_clip_norm": 0.1,
            "actor_clip_norm": 0.1,
        },
        value_func=mlp_q,
        policy=policy,
        name=name + '_ddpg',
        replay_buffer=None
    )

    mlp_dyna = ContinuousMLPGlobalDynamicsModel(
        env_spec=env_spec,
        name_scope=name + '_mlp_dyna',
        name=name + '_mlp_dyna',
        output_low=env_spec.obs_space.low,
        output_high=env_spec.obs_space.high,
        learning_rate=0.01,
        mlp_config=[
            {
                "ACT": "RELU",
                "B_INIT_VALUE": 0.0,
                "NAME": "1",
                "L1_NORM": 0.0,
                "L2_NORM": 0.0,
                "N_UNITS": 16,
                "TYPE": "DENSE",
                "W_NORMAL_STDDEV": 0.03
            },
            {
                "ACT": "LINEAR",
                "B_INIT_VALUE": 0.0,
                "NAME": "OUPTUT",
                "L1_NORM": 0.0,
                "L2_NORM": 0.0,
                "N_UNITS": env_spec.flat_obs_dim,
                "TYPE": "DENSE",
                "W_NORMAL_STDDEV": 0.03
            }
        ])
    algo = Dyna(env_spec=env_spec,
                name=name + '_dyna_algo',
                model_free_algo=ddpg,
                dynamics_model=mlp_dyna,
                config_or_config_dict=dict(
                    dynamics_model_train_iter=10,
                    model_free_algo_train_iter=10
                ))
    # For examples only, we use random reward function and terminal function with fixed episode length.
    algo.set_terminal_reward_function_for_dynamics_env(
        terminal_func=FixedEpisodeLengthTerminalFunc(max_step_length=env.unwrapped._max_episode_steps,
                                                     step_count_fn=algo.dynamics_env.total_step_count_fn),
        reward_func=RandomRewardFunc())
    agent = Agent(env=env, env_spec=env_spec,
                  algo=algo,
                  algo_saving_scheduler=PeriodicalEventSchedule(
                      t_fn=lambda: get_global_status_collect()('TOTAL_AGENT_TRAIN_SAMPLE_COUNT'),
                      trigger_every_step=20,
                      after_t=10),
                  name=name + '_agent',
                  exploration_strategy=EpsilonGreedy(action_space=env_spec.action_space,
                                                     init_random_prob=0.5))

    flow = create_dyna_flow(
        train_algo_func=(agent.train, (), dict(state='state_agent_training')),
        train_algo_from_synthesized_data_func=(agent.train, (), dict(state='state_agent_training')),
        train_dynamics_func=(agent.train, (), dict(state='state_dynamics_training')),
        test_algo_func=(agent.test, (), dict(sample_count=10)),
        test_dynamics_func=(agent.algo.test_dynamics, (), dict(sample_count=10, env=env)),
        sample_from_real_env_func=(agent.sample, (), dict(sample_count=10,
                                                          env=agent.env,
                                                          in_which_status='TRAIN',
                                                          store_flag=True)),
        sample_from_dynamics_env_func=(agent.sample, (), dict(sample_count=10,
                                                              env=agent.algo.dynamics_env,
                                                              in_which_status='TRAIN',
                                                              store_flag=True)),
        train_algo_every_real_sample_count_by_data_from_real_env=10,
        train_algo_every_real_sample_count_by_data_from_dynamics_env=10,
        test_algo_every_real_sample_count=10,
        test_dynamics_every_real_sample_count=10,
        train_dynamics_ever_real_sample_count=10,
        start_train_algo_after_sample_count=1,
        start_train_dynamics_after_sample_count=1,
        start_test_algo_after_sample_count=1,
        start_test_dynamics_after_sample_count=1,
        warm_up_dynamics_samples=1
    )

    experiment = Experiment(
        tuner=None,
        env=env,
        agent=agent,
        flow=flow,
        name=name + '_exp'
    )
    experiment.run()


from baconian.core.experiment_runner import single_exp_runner

GlobalConfig().set('DEFAULT_LOG_PATH', './log_path')
single_exp_runner(task_fn, del_if_log_path_existed=True)
