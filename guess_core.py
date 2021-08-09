import configparser
import os
import re
__version__ = "2021-08-06"

#settings is forbidden to import

class guess(object):
    def __init__(self):
        self.guessmodel = self.get_model()
        self.config = configparser.ConfigParser()
        self.config2()


    def config2(self):
        if os.path.exists('config.ini'):
            # self.config.read('config.ini', encoding='utf-8')
            self.config.read('config.ini')
        else:
            self.config.add_section('unallocated')
            self.config.set('unallocated', 'AccountName', '未分配')
            self.config.set('unallocated', 'AccountPosition', '0')
            self.config.set('unallocated', 'keywords', "'关键词1','关键词2','use_comma_to_split_the_keywords','using 双引号 around the keywords'")
            self.config.write(open('config.ini', 'w'))

    def get_model(self):
        try:
            config2 = configparser.ConfigParser()
            config2.read('settings.ini')
            return int(config2.getint( "data","guess_model_value"))
        except:
            return 1

    def get(self, *info): # this is the core of the guess
        infos = " ".join(list(map(lambda x: str(x), info)))
        # print(infos)
        unguessed = 'unallocated'
        allsections = self.config.sections()
        if self.guessmodel == 1:
            try:
                for section in allsections:
                    kws = self.config.get(section, 'keywords')
                    kwlist = eval(kws)
                    for kw in kwlist:
                        if re.search(kw, infos, re.I):
                            return section
                else:
                    return unguessed
            except:
                return unguessed
        else:
            sec=[]
            try:
                for section in allsections:
                    sec_kw_count=0
                    kws = self.config.get(section,'keywords')
                    kwlist=eval(kws)
                    for kw in kwlist:
                        if re.search(kw,infos,re.I):
                            sec_kw_count = sec_kw_count +1
                    sec.append(sec_kw_count)
                # print(list(zip(allsections,sec)))
                return allsections[sec.index(max(sec))]

            except:
                return unguessed

    def initiate_setting(self):
        allsections = self.config.sections()
        return dict(zip(allsections, [self.config.getint(allsections[i], 'accountposition') for i in range(len(allsections))]))


if __name__ == '__main__':
    print(guess().get('eason he','miriam Xu',"legend",'linekong','ella w du','chris xa wang','蓝港'))