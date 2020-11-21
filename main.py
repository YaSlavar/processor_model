import re


class PROCESSOR:
    def __init__(self, commands, data, compile=False):
        self.digit_capacity = 16

        self.if_compile = compile
        self.data = data
        self.commands = commands

        self.commands_len = 0

        # Начальные значения регистров
        self.registry = {
            'ax': 0,  # операнд 1
            'bx': 0,  # операнд 2
            'cx': 0,  # счетчик цикла
            'dx': 0,  # индекс массива данных
            'ex': 0,

            'al': 0,  # первый множитель
            'bl': 0,  # второй множитель

            'be': False,  # регистр сравнения
            'pc': 0,  # счетчик комманд
            'cf': False  # флаг переполнения
        }

        # Адреса регистров
        self.registry_links = {
            '0001': "ax",
            '0010': "bx",
            '0011': 'cx',
            '0100': 'dx',
            '0101': 'ex',
            '0110': "be",

            '0111': "al",
            '1000': "bl"
        }

        # Адреса команд
        self.command_links = {
            '0001': 'mov',
            '0010': 'cmp',
            '0011': 'jbe',
            '0100': 'add',
            '0101': 'loop',
            '0110': 'mul',
            '0111': 'adc'
        }

    def find_destination(self, literal, operator):
        """Получение ссылки на оператор"""

        if literal == '0001':  # используем регистры, возвращаем название регистра
            return self.registry_links[operator]

        elif literal == '0010':  # используем память, возвращаем индекс в памяти
            operator_index = int(operator, 2)
            return operator_index

        elif literal == '0100':  # используем литерал
            return self.registry_links[operator]

        else:
            return operator

    def get_value(self, data_index, literal, operator_link):
        """Получение значения оператора"""
        if literal == '0001':  # используем регистры, возвращаем значение регистра
            return self.registry[operator_link]

        elif literal == '0010':  # используем память, возвращаем индекс в памяти
            return self.data[data_index][operator_link]

        elif literal == '0011':  # получаем значение напрямую
            return int(operator_link, 2)

        elif literal == '0100':  # получение значения из памяти по индексу из регистра
            value_index = self.get_value(data_index, '0001', operator_link)
            return self.data[data_index][value_index]

    # КОМАНДЫ {
    def mov(self, data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2):
        """Перемещение значения в регистр/память"""
        if literal1 == '0001':  # если адресат занчения - регистр
            self.registry[link_to_operator1] = self.get_value(data_index2, literal2, link_to_operator2)
        elif literal1 == '0010':  # если адресат занчения - память
            self.data[data_index1][link_to_operator1] = self.get_value(data_index2, literal2, link_to_operator2)

    def cmp(self, data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2):
        """Сравнение операторов"""

        def cmp_op(op1, op2):
            return op1 < op2

        value1 = self.get_value(data_index1, literal1, link_to_operator1)
        value2 = self.get_value(data_index2, literal2, link_to_operator2)
        self.registry['be'] = cmp_op(value1, value2)

    def jbe(self):
        """Прыжок через команду"""
        if not self.registry['be']:
            self.registry['pc'] += 1

    def add(self, data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2):
        """Сложение"""
        result = self.get_value(data_index1, literal1, link_to_operator1) + self.get_value(data_index2, literal2,
                                                                                           link_to_operator2)
        if literal1 == '0001':  # если адресат занчения - регистр
            self.registry[link_to_operator1] = result
        elif literal1 == '0010':  # если адресат занчения - память
            self.data[data_index1][link_to_operator1] = result

    def loop(self, bin_link_to_op1):
        """Цикл"""
        if self.registry['cx'] > 1:
            self.registry['pc'] = int(bin_link_to_op1, 2) - 1
        self.registry['cx'] -= 1

    def adc(self, data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2):
        """Сложение с переносом"""
        self.registry['cf'] = False  # Сброс флага переполнения

        result = self.get_value(data_index1, literal1, link_to_operator1) + self.get_value(data_index2, literal2,
                                                                                           link_to_operator2)
        if literal1 == '0001':  # если адресат занчения - регистр
            if self.get_digit_capacity(result) <= self.digit_capacity:  # нет переполнения, пишем в первый операнд
                self.registry[link_to_operator1] = result
            else:  # переполнение
                self.registry['ax'] = self.get_max_value_by_digit_capacity(self.digit_capacity)  # основная часть
                self.registry['dx'] = result - self.get_max_value_by_digit_capacity(self.digit_capacity)  # переполнение

                self.registry['cf'] = True

        elif literal1 == '0010':  # если адресат занчения - память
            self.data[data_index1][link_to_operator1] = result

    def mul(self, data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2):
        """Умножение с переносом"""
        self.registry['cf'] = False  # Сброс флага переполнения

        result = self.get_value(data_index1, literal1, link_to_operator1) * self.get_value(data_index2, literal2,
                                                                                           link_to_operator2)
        if literal1 == '0001':  # если адресат занчения - регистр
            if self.get_digit_capacity(result) <= self.digit_capacity:  # нет переполнения, пишем в первый операнд
                self.registry[link_to_operator1] = result
            else:  # переполнение
                self.registry['ax'] = self.get_max_value_by_digit_capacity(self.digit_capacity)  # основная часть
                self.registry['dx'] = result - self.get_max_value_by_digit_capacity(self.digit_capacity)  # переполнение

                self.registry['cf'] = True

        elif literal1 == '0010':  # если адресат занчения - память
            self.data[data_index1][link_to_operator1] = result

    # } КОМАНДЫ

    @staticmethod
    def hex_to_bin(command_line_hex):
        return bin(int(command_line_hex[2:], 16))[2:].zfill(28)

    @staticmethod
    def bin_to_hex(command_line_bin):
        return hex(int(command_line_bin, 2))[2:]

    @staticmethod
    def dec_to_bin(command_line_bin):
        return bin(int(command_line_bin))[2:]

    @staticmethod
    def dec_to_hex(command_line_bin):
        return PROCESSOR.bin_to_hex(PROCESSOR.dec_to_bin(command_line_bin))

    @staticmethod
    def get_digit_capacity(num):
        return len(bin(num)[2:])

    @staticmethod
    def get_max_value_by_digit_capacity(digit_capacity):
        return pow(2, digit_capacity)

    def compile(self):
        """Компиляция"""

        def set_literal_and_address(operator):
            """Установка значения литерала по оператору
            :return номер массива памяти, литерал, адрес
            """
            # Если оператор содержится в адресах регистров, тогда литерал = 1, а значение = адрес регистра
            for key, value in self.registry_links.items():
                if value == operator:
                    return '0', '1', str(int(key, 2))

            # Если оператор содержит ссылку на память (data), тогда
            data_link = re.findall(r'data_\d+_\[(.+)\]', operator)
            if data_link:
                data_source = re.findall(r'_(\d+)_', operator)
                # если прямой индекс
                if re.findall(r'[\d+]', data_link[0]):
                    return data_source[0], '2', data_link[0]
                # ссылка на регистр
                else:
                    data_index, literal, address = set_literal_and_address(data_link[0])
                    return data_source[0], '4', address

            # Если оператор = чило, тогла литерал = 3, а значаение = operator
            if re.findall(r'\d+', operator):
                return '0', '3', operator

        hex_command_list = []

        for num, command in enumerate(self.commands):
            data_index1, data_index2, literal1, literal2, address1, address2 = '0', '0', '0', '0', '0', '0'

            command = command.replace(', ', ' ')
            split_command = command.split(' ')

            instruction = split_command[0]

            operator1 = split_command[1]
            data_index1, literal1, address1 = set_literal_and_address(operator1)
            if len(split_command) == 3:
                operator2 = split_command[2]
                data_index2, literal2, address2 = set_literal_and_address(operator2)

            hex_command = '0x'

            for address_item, instruction_item in self.command_links.items():
                if instruction == instruction_item:
                    hex_command += self.bin_to_hex(address_item)

            hex_command += data_index1
            hex_command += data_index2
            hex_command += literal1
            hex_command += literal2
            hex_command += address1
            hex_command += address2

            hex_command_list.append(hex_command)
            print("{}: HEX: {} BIN: {}".format(num, hex_command, self.hex_to_bin(hex_command)))
        return hex_command_list

    def run(self):
        """Выполнение комманд"""
        # Если на входе ассемблер
        if self.if_compile:
            print("Компиляция")
            self.commands = self.compile()
            print("\n")

        # Задаем количество команд
        self.commands_len = len(self.commands)

        print(self.registry)
        # цикл по коммандам
        while self.registry['pc'] < self.commands_len:
            command_line_hex = self.commands[self.registry['pc']]  # Команда в 16 ричном виде
            command_line_bin = self.hex_to_bin(command_line_hex)  # Команда в 2 чном виде

            # Разбор команды на составляющие (номер, литералы, ссылки на операторы)
            command = command_line_bin[0:4]
            bin_data_index1 = command_line_bin[4:8]
            bin_data_index2 = command_line_bin[8:12]
            literal1 = command_line_bin[12:16]
            literal2 = command_line_bin[16:20]
            bin_link_to_op1 = command_line_bin[20:24]
            bin_link_to_op2 = command_line_bin[24:28]

            # получаем ссылку на регистр/на ячейку памяти
            link_to_operator1 = self.find_destination(literal1, bin_link_to_op1)
            link_to_operator2 = self.find_destination(literal2, bin_link_to_op2)

            print("command_line_hex: {}\n"
                  "command_line_bin: {}\n"
                  "command: {} ({})\n"
                  "data_index1: {}\n"
                  "data_index1: {}\n"
                  "literal1: {}\n"
                  "literal2: {}\n"
                  "operator1: {}\n"
                  "operator2: {}\n".format(command_line_hex, command_line_bin, command, self.command_links[command],
                                           bin_data_index1,
                                           bin_data_index2,
                                           literal1, literal2, bin_link_to_op1, bin_link_to_op2))

            data_index1 = int(bin_data_index1, 2)
            data_index2 = int(bin_data_index2, 2)

            if command == '0001':  # mov op1 <- op2
                self.mov(data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2)

            if command == '0010':  # cmp op1 < op2
                self.cmp(data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2)

            if command == '0011':  # jbe be
                self.jbe()

            if command == '0100':  # add op1 <- op2
                self.add(data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2)

            if command == '0101':  # loop pc
                self.loop(bin_link_to_op1)

            if command == '0110':  # mul op1 <- op2
                self.mul(data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2)

            if command == '0111':  # adc op1 <- op2
                self.adc(data_index1, data_index2, literal1, literal2, link_to_operator1, link_to_operator2)

            self.registry['pc'] += 1

            print(self.registry)
            for index, value in enumerate(self.data):
                print('data_{} : {}'.format(index, value))
            print("\n")

        for index, value in enumerate(self.data):
            print('data_{} : {}'.format(index, value))
        print("\n")


if __name__ == "__main__":
    # # Лаб. работа №1
    # commands = [
    #     "0x1001211",  # mov reg data ax data[1]
    #     "0x1001230",  # mov reg data сx data[0] инициализация кол-ва итераций в цикле
    #     "0x1001342",  # mov reg var  dx 2
    #
    #     "0x1001424",  # mov reg data bx data[dx]
    #     "0x2001112",  # cmp reg reg ax bx
    #     "0x3001050",  # jbe reg be
    #     "0x1001112",  # mov reg reg ax bx
    #     "0x4001341",  # add reg var dx 1
    #     "0x5003030"  # loop reg 3
    # ]
    #
    # data = [
    #     [4, 5, 2, 1, 7, 6]
    # ]
    #
    # processor = PROCESSOR(commands, data, compile=False)
    # processor.run()
    #
    # del processor
    #
    # # Лаб. работа №3
    # commands = [
    #     'mov ax, data_0_[1]',
    #     'mov cx, data_0_[0]',  # инициализация кол-ва итераций в цикле
    #     'mov dx, 2',
    #
    #     'mov bx, data_0_[dx]',
    #     'cmp ax, bx',
    #     'jbe be',
    #     'mov ax, bx',
    #     'add dx 1',
    #     'loop 3'
    # ]
    #
    # data = [
    #     [4, 5, 2, 1, 7, 6]
    # ]
    #
    # processor = PROCESSOR(commands, data, compile=True)
    # processor.run()
    #
    # del processor

    # Лаб. работа №2
    commands = [
        'mov cx, 5',  # инициализация кол-ва итераций в цикле
        'mov ex, 0',  # инициализация индекса массива памяти

        'mov ax, data_0_[ex]',  # в регистр AX EX-ный элемент массива 0
        'mov bx, data_1_[ex]',  # в регистр BX EX-ный элемент массива 1

        'mul ax bx',
        # произведение EX-ный элемент массива 0 и EX-ный элемент массива 1
        # => результат: основная часть в AX, при переполнении + в DX

        'adc data_2_[0] ax',
        # складываем основную часть в 64битную память )))))0) (мой процессор, могу себе позволить 64 битную память!!!)
        'adc data_2_[1] dx',
        # складываем переполняемую часть в 64битную память

        'add ex 1',  # смещаем индекс массивов на 1
        'loop 2',  # прыжок на 2ю команду

        # когда завершили сверку, складываем в памяти основную часть результата и переполняемую
        'adc data_2_[0] data_2_[1]'
        # результат в data_2[0]
    ]

    data = [
        [65535, 2, 3, 4, 5],
        [2, 2, 3, 4, 5],
        [0, 0]
    ]

    processor = PROCESSOR(commands, data, compile=True)
    processor.run()
