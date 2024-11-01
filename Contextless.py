import os
from openai import OpenAI
from time import sleep
import configparser
import services.utils as utility
import services.dafny_verifyer as verifier


# 读取配置文件
def get_config():
    cur_dir_path = os.getcwd()
    config_path = os.path.join(cur_dir_path, 'env.config')
    if not (os.path.exists(config_path)):
        print("env.config not found!!")
        return
    config = configparser.ConfigParser()
    config.read(config_path)

    api_config = dict()
    api_config["openai_api_key"] = config.get('DEFAULT', 'openai_api_key')
    api_config["openai_base_url"] = config.get('DEFAULT','openai_base_url')
    api_config["model"] = config.get('DEFAULT', 'model')
    api_config["temp"] = float(config.get('DEFAULT', 'temp'))

    env_config = dict()
    env_config["K_run"] = config.get('DEFAULT', 'K_run')
    env_config["cool_down_time"] = config.get('DEFAULT', 'cool_down_time')
    data_path = os.path.join(cur_dir_path, config.get('DEFAULT','data_path'))
    env_config["data_path"] = data_path
    base_output_path = os.path.join(cur_dir_path,config.get('DEFAULT', 'base_output_path'))
    env_config["base_output_path"] = base_output_path

    return api_config, env_config

# 每个任务生成save_map 包括task内容，k，问题描述，response，生成的统计(Json), Dafny代码(.dfy为结尾)两个文件
def get_output_paths(_task, _temp, _K, _model, _base_path):
    out_paths = dict()
    common_path = "task_id" + "_" + str(_task['task_id']) + "-" + _model + "-" + "temp_" + str(
        _temp) + "-" + "k_" + str(_K)
    out_paths["saved_path"] = os.path.join(_base_path, common_path + ".json")
    out_paths["dfy_src_path"] = os.path.join(_base_path, common_path + ".dfy")
    out_paths["verification_path"] = os.path.join(_base_path, common_path + "_verification_log.txt")

    return out_paths


def get_context_less_prompt_template(_task):
    cur_path = os.getcwd()
    prompt_path = os.path.join(cur_path, 'templates/CONTEXTLESS_TEMPLATE.file')
    if not (os.path.exists(prompt_path)):
        print("file not found!!")
        return
    template = utility.read_file(prompt_path)
    final_prompt = template.format(task_description=_task['task_description'])
    print(final_prompt)
    return final_prompt


def invoke_gpt4(_task, _temp, _key, _url):
    prompt_ = get_context_less_prompt_template(_task)
    client = OpenAI(
        # This is the default and can be omitted
        api_key=_key,
        base_url=_url
    )
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_,
            }
        ],
        model="gpt-4o-mini",
        temperature=_temp
    )
    result = completion.choices[0].message.content
    print(result)
    return result




def prepare_model_response(_task, _temp, _K, _res, _model, _dafny_code,  _verification_bits):
    saved_map = {
        "id": _task['task_id'],
        "K": _K,
        "temperature": _temp,
        "task_id": _task['task_id'],
        "task_description": _task['task_description'],
        "model": _model,
        "response": _res,
        "dafny_code": _dafny_code,
        "verification_bits": _verification_bits
    }
    return saved_map


def execute_context_less_prompt(_api_config, _env_config):
    all_response = []
    test_path = os.path.join(_env_config['data_path'],"test-task.json")
    tasks = utility.load_json(test_path)
    model = _api_config['model']
    for t in tasks:
        task = tasks[t]
        print("Prompting Task: " + task['task_id'])
        # k_run指的是尝试k次，源代码逻辑尝试到verify出正确的就停止了。
        for run_count in range(1, int(_env_config["K_run"]) + 1):
            output_paths = get_output_paths(_task=task, _temp=_api_config["temp"], _K=run_count,
                                            _model=model,
                                            _base_path=_env_config["base_output_path"])
            try:
                response = ""
                if model == "gpt-4":
                    response = invoke_gpt4(_task=task, _temp=_api_config['temp'],
                                           _key=_api_config['openai_api_key'], _url=_api_config['openai_base_url'])

                parsedCode = verifier.verify_dfy_src(response, output_paths['dfy_src_path'])
                verification_bits = verifier.get_all_verification_bits_count(parsedCode)
                saved_map = prepare_model_response(_task=task, _temp=_api_config['temp'], _K=run_count, _res=response,
                                                   _model=model, _dafny_code=parsedCode,
                                                   _verification_bits=verification_bits)
                utility.save_to_json(saved_map, output_paths["saved_path"])
                all_response.append(saved_map)
                if run_count == int(_env_config["K_run"]):
                    all_response.append(saved_map)
                utility.save_to_json(saved_map, output_paths["saved_path"])
            except Exception as e:
                print("Error while processing => " + task['task_id'] + "in temperature =>" + str(
                    _api_config['temp']) + str(e))
            sleep(int(_env_config['cool_down_time']))
    utility.save_to_json(all_response,
                         os.path.join(_env_config["base_output_path"],
                                      "gpt4-contextleass-prompting-" + model + ".json"))


if __name__ == '__main__':
    api_config, env_config = get_config()
    execute_context_less_prompt(api_config, env_config)
    print("Done")
