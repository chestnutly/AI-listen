# encoding=utf-8
import os
import re
import shutil
import subprocess
# import search_dict
import time


def X_seg_runner(data_dir=r'..\Data', target_dir=r'..\after_seg'):
    """
    无返回值，直接调用run_segment函数，并将两个参数传入其中，对文件进行切分

    Args:
        data_dir: 存放用户音频的文件夹，默认为上一级中的Data，可以修改
        target_dir: 存放切分并提取过的数据的文件夹，默认为上一级中的after_seg文件夹，可以修改
    """
    class ErrorSeg(Exception):
        """
        异常类型，当数据异常时出现

        Attributes:
            wav: 异常的音频文件
            txt: 异常的文本文件
        """
        def __init__(self, wav, txt):
            self.wav = wav
            self.txt = txt

        def __str__(self):
            print('Wrong with', self.txt, 'and', self.wav)

    def preprocess_data(path):
        """
        统一对音频的文文件进行处理，包括大小写转化、非英文符号替换；

        Args:
            path: 用户预设的数据文件夹，包括.wav文件、.txt文件、.dict文件
        """
        all_files = os.listdir(path)
        for file in all_files:
            temp = ''
            if '.txt' in file:
                with open(path + r'\\' + file, 'r', encoding='utf-8') as fr:
                    lines = fr.read().rstrip().lower()
                    for i in lines:
                        if i != "’":
                            temp = temp + i
                        else:
                            temp = temp + "'"
                    fr.close()
                with open(path + r'\\' + file, 'w') as fw:
                    fw.write(temp)

    def get_dic_name(data_path):
        """
        从用户的数据文件夹中寻找词典文件，并将词典文件拷贝至上级目录中对Dictionary文件夹

        Args:
            data_path: 用户预设的数据文件夹，函数将对该文件夹进行遍历寻找词典文件
        Returns:
            file: 词典文件名称
        """
        upper_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_list = os.listdir(data_path)
        dic_list = os.listdir(upper_path + '\\' + 'Dictionary')
        for file in data_list:
            if '.dict' in file:
                if file not in dic_list:
                    shutil.copy(data_path + '\\' + file, upper_path + '\\' + 'Dictionary')
                return file

    def set_path(data_path):
        """
        初始化X_segment文件路径，使得切分程序可以在任意文件夹、盘符下运行；主要修改setting.ini中的数据文件夹和词典路径

        Args:
            data_path: 用户数据文件夹
        """
        upper_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        temp_path = upper_path + '\\' + 'temp_seg'
        dic_path = upper_path + '\\' + 'Dictionary' + '\\' + get_dic_name(upper_path + '\\' + 'Dictionary')
        setting_path = '../xSegmenter-final/setting.ini'
        file = open(setting_path, 'r')
        content = file.readlines()
        file.close()
        revise_data = 'dataFilePath=' + temp_path
        revise_dic = 'dictFileName=' + dic_path
        content[122] = re.sub('^dataFilePath=(.*)', repr(revise_data), content[122])
        content[122] = content[122].replace("'", '')
        content[125] = re.sub('^dictFileName=(.*)', repr(revise_dic), content[125])
        content[125] = content[125].replace("'", '')
        file = open(setting_path, 'w')
        file.write(''.join(content))

    def get_data_list(data_list):
        """
        输入用户数据文件夹中的文件列表，得到.txt文件列表和.wav文件列表

        Args:
            data_list: 数据文件夹中的文件列表，即数据文件夹中的所有数据名
        Returns:
            txt_list: .txt文件列表
            wav_list: .wav文件列表
        """
        txt_list = []
        wav_list = []
        for file in data_list:
            if '.txt' in file:
                txt_list.append(file)
            if '.wav' in file:
                wav_list.append(file)
        return txt_list, wav_list

    def init_x_seg(first_use=False):
        """
        初始化Xsegmenter，删除xSegmenter-final文件夹中的DATA、HMM、TEMP文件夹和所有内容，使程序可以反复自动运行

        Args:
            first_use: 检测是否是第一次在本脚本中运行xSegmenter，如果是，则清空temp_seg, after_seg中的所有内容，防止文件移动时产生的报错
        """
        seg_dir = '..\\xSegmenter-final'
        all_dirs = os.listdir(seg_dir)
        after_seg = '..\\after_seg'
        fin_list = os.listdir(after_seg)
        temp_seg = '..\\temp_seg'
        temp_list = os.listdir(temp_seg)
        if first_use:
            for file in fin_list:
                os.remove(after_seg+'\\'+file)
        for file in temp_list:
            os.remove(temp_seg+'\\'+file)
        if 'DATA' in all_dirs:
            shutil.rmtree(seg_dir + '\\' + 'DATA')
            shutil.rmtree(seg_dir + '\\' + 'TEMP')

    def seg_path():
        """
        设置xSegmenter路径，将相对路径转换为绝对路径，使可以使用os.system函数调用

        Returns:
            返回xSegmenter的绝对路径
        """
        upper_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return upper_path + '\\' + 'xSegmenter-final\\xSegmenter.exe'

    def move_to_target(temp_dir, tar_dir):
        """
        将已处理完的数据从temp_seg文件夹移动至after_seg文件夹，以便praat进行处理

        Args:
            temp_dir: temp_seg文件夹
            tar_dir: after_seg文件夹
        """
        all_files = os.listdir(temp_dir)
        for file in all_files:
            if tar_dir != r'..\after_seg':
                shutil.copy(temp_dir + '\\' + file, r'..\after_seg')
            shutil.move(temp_dir + '\\' + file, tar_dir)

    def run_segment(data_paths, target_paths):
        """ 调用xSegmenter文件夹，整合先前的函数进行数据统一处理

        首先初始化xSegmenter，设置好相关路径，得到文件列表；遍历.txt列表和.wav列表，逐对处理音频和文本文件，生成切割后的.TextGrid文件，输出
        到after_seg文件夹

        Args:
            data_paths: 存放用户音频的文件夹，默认为上一级中的Data，由X_seg_runner传入
            target_paths: 存放切分并提取过的数据的文件夹，默认为上一级中的after_seg文件夹，由X_seg_runner传入

        Raises:
            ErrorSeg: 当音频/文本文件有误导致无法切割时，触发该异常；
        """
        init_x_seg(True)
        temp_dir = '../temp_seg'
        seg_dir = seg_path()
        data_list = os.listdir(data_paths)
        preprocess_data(data_paths)
        txt_list, wav_list = get_data_list(data_list)
        set_path(data_paths)
        for txt_file, wav_file in zip(txt_list, wav_list):
            init_x_seg()
            shutil.copy(data_paths + '/' + txt_file, temp_dir)
            shutil.copy(data_paths + '/' + wav_file, temp_dir)
            try:
                os.system(seg_dir)
                all_file = os.listdir(temp_dir)
                for file in all_file:
                    if '.TextGrid' not in file:
                        # os.system('taskkill /IM xSegmenter.exe /F')
                        raise ErrorSeg(txt_file, wav_file)
                    else:
                        break
                move_to_target(temp_dir, target_paths)
            except ErrorSeg:
                print('Error with data', txt_file, 'and', wav_file)
                # search_dict.search_unk()
                # init_x_seg()
                # os.system(seg_dir)
                continue
    run_segment(data_dir, target_dir)


def praat_runner(target_path=None):
    """
    调用praat_all函数，将提取后的数据传输至用户指定的输出文件夹

    Args:
        target_path: 用户指定的目标文件夹，默认为None（即输出到默认路径）；如果存在值则将数据输出至用户指定路径
    """
    class FailExtraction(BaseException):
        """
        Attributes:
            wav: 异常的.wav文件名
            grid: 异常的.TextGrid文件名
        """
        def __init__(self, wav, grid):
            self.wav_file = wav
            self.grid_file = grid

        def __str__(self):
            print("Wrong with data", self.wav_file, 'and', self.grid_file)

    def get_upper_path():
        """
        得到脚本的上级目录，以便后续操作

        Returns:
            upper_path: 脚本上级目录
        """
        upper_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return upper_path

    def run_praat(praat):
        """
        调用Praat，从指定的.wav、.TextGrid中提取项目需要的音频参数

        Args:
            praat: praat程序地址
        """
        func_script = get_upper_path() + '\\' + 'temp_praat' + '\\' + 'call_run_praat.praat'
        subprocess.call([praat, '--run', func_script])

    def extract_data(praat):
        """
        调用Praat，对run_praat脚本中得到的声学数据进行统一汇总，得到BID.txt, velocity.txt等文件

        Args:
            praat: praat程序地址
        """
        func_script = get_upper_path() + '\\' + 'Final' + '\\' + 'call_ext_praat.praat'
        subprocess.call(([praat, '--run', func_script]))

    def get_file_list(file_lis, file_name):
        """得到相同名称前缀的数据文件列表

        在调用过run_praat函数，会生成大量的和音频、文本文件同前缀名称的不同格式的文件，因此要遍历这些文件得到一个同前缀的文件列表
        辅助后续的程序运行

        Args:
            file_lis: 数据文件夹中的文件列表，即数据文件夹中的所有数据名
            file_name: 文件名，可以是.TextGrid文件或者.wav文件

        Returns:
            all_files: 所有包含file_name文件前缀的数据文件

        Examples:
            Input: (['123.TextGrid', '123.wav'], '123.wav')
            Output: ['123.TextGrid', '123.Label', '123.BID', ... , '123.wav']
        """
        former_name = file_name.split('.')[0]
        all_files = []
        for file in file_lis:
            if former_name in file:
                all_files.append(file)
        return all_files

    def get_wav_grid(file_lis):
        """
        得到包含所有的.wav和.TextGrid文件的列表

        Args:
            file_lis: 包含所有文件的列表

        Returns:
            wav_lis: .wav文件列表
            grid_lis: .TextGrid文件列表
        """
        wav_lis = []
        grid_lis = []
        for file in file_lis:
            if '.wav' in file:
                wav_lis.append(file)
            if '.TextGrid' in file:
                grid_lis.append(file)
        return wav_lis, grid_lis

    def process_bar(length, position, wav, text_grid):
        """
        在文件数大于10时生成进度条，显示数据处理进度

        Args:
            length: 文件数量（包含所有的.TextGrid, .wav文件）
            position: 当前文件位置
            wav: .wav文件名
            text_grid: .TextGrid文件名
        :return:
        """
        status = 0
        if length >= 100:
            status = 50
        else:
            status = 10
        period = length // status
        for i in range(status):
            if i * period <= position <= (i + 1) * period:
                a = '*' * (i + 1)
                b = '.' * (status - i - 1)
                pr_bar = 'Processing: [' + a + b + ']; Files are: ' + wav + ' and ' + text_grid
                print(pr_bar)

    def init_praat():
        """初始化praat

        检测temp_praat和Final文件夹，若不为空则清空删除文件夹中的所有文件，防止报错
        """
        temp = '..\\temp_praat'
        final = '..\\Final'
        temp_list = os.listdir(temp)
        final_list = os.listdir(final)
        if len(temp_list) != 0:
            for file in temp_list:
                os.remove(temp + '\\' + file)
        if len(final) != 0:
            for file in final_list:
                os.remove(final + '\\' + file)

    def praat_all(final=None):
        """调用Praat对所有的数据进行处理

        首先初始化praat防止报错，设置目标路径（用户可以自定义）；将所有的.wav和.TextGrid文件统一移至temp_praat文件夹，调用praat对文件
        进行统一处理；

        Args:
            final: 用户指定的目标数据输出路径，如果未指定则为None，并将数据输出到上级Final文件夹

        Raises:
            FailExtraction: 数据异常导致无法提取数据时报出此异常；并将出错的数据名存入error_data文件夹中并向用户反馈

        """
        init_praat()
        target_path = r'..\\Final'
        move_tools(target_path)
        praat = get_upper_path() + '\\' + 'Praat' + '\\' + 'praat6137_win64.exe'
        print('----- Now Running -----')
        file_path = get_upper_path() + '\\' + 'after_seg'
        file = os.listdir(file_path)
        wav_list, grid_list = get_wav_grid(file)
        temp_path = get_upper_path() + '\\' + 'temp_praat'
        ext_path = target_path
        error_data = []
        sums = len(file)
        num = 0
        for i, j in zip(wav_list, grid_list):
            num += 2
            process_bar(sums, num, i, j)
            ori_grid_path = file_path + '\\' + i
            ori_raw_path = file_path + '\\' + j
            shutil.copy2(ori_grid_path, temp_path)
            shutil.copy2(ori_raw_path, temp_path)
            try:
                run_praat(praat)
                if len(os.listdir(temp_path)) < 21:
                    raise FailExtraction(i, j)
            except FailExtraction:
                error_data.append(i)
                error_data.append(j)
                all_files = get_file_list(os.listdir(temp_path), i)
                for file in all_files:
                    os.remove(temp_path + '\\' + file)
                continue
            all_files = get_file_list(os.listdir(temp_path), i)
            for file in all_files:
                shutil.move(temp_path + '\\' + file, ext_path)
        extract_data(praat)
        print('Data extracted!')
        if len(error_data) != 0:
            print("There're some errors with your data: ")
            for file in error_data:
                print(file)
            print('Please check')
        move_to_target(target_path, final)

    def move_tools(target_dir):
        """
        将call_run_praat.praat、ProsodyPro 提取归一化基频数据及情感语音参数.praat、'call_ext_praat.praat'脚本从tools文件夹中转移
        到待使用的文件夹

        Args:
            target_dir: 目标文件夹，即call_ext_praat.praat文件夹转移的目标文件夹
        """
        tools = '..\\Tools'
        main_tool = 'ProsodyPro 提取归一化基频数据及情感语音参数.praat'
        temp_dir = '..\\temp_praat'
        tool_list = os.listdir(tools)
        for file in tool_list:
            if file != 'call_ext_praat.praat':
                shutil.copy(tools + '\\' + file, temp_dir)
            else:
                shutil.copy(tools + '\\' + main_tool, '..\\Final')
                shutil.copy(tools + '\\' + file, '..\\Final')

    def move_to_target(default_dir, target_dir):
        """
        将已处理的所有用户数据转移至用户指定的目标文件夹

        Args:
            default_dir: 默认文件夹，即Final文件夹
            target_dir: 目标文件夹，由用户自定义
        """
        if not target_dir:
            return
        else:
            all_data = os.listdir('..\\Final')
            for file in all_data:
                shutil.move('..\\Final' + '\\' + file, target_dir)

    if not target_path:
        praat_all(target_path)
    else:
        praat_all()


def data_extractor(data_dir='..\\Praat\\data\\voice', target_dir='..\\Final'):
    """
    调用xSegmenter和praat对数据进行统一提取

    Args:
        data_dir: 数据文件夹，包括.wav和.txt文件
        target_dir: 所有数据提取完转移的目标文件夹
    :return:
    """
    if 'PythonFile' in os.getcwd():
        X_seg_runner(data_dir)
        praat_runner(target_dir)
    else:
        os.chdir('./PythonFile')
        X_seg_runner(data_dir)
        praat_runner(target_dir)
        os.chdir('..')


if __name__ == '__main__':
    """
    程序debug使用
    """
    data_extractor()
