# StreamToAscii

I. StreamToAscii-Parallel
1. 在此脚本目录创建[position.json]及[stream.json]
2. [position.json]用于自动导出PAC系统的wfs波形文件，[stream.json]用于计算导出的波形流数据
3. [position.json]中配置模板（#及其后的文字删除）：
{
  "INPUT": "",			#PAC系统的wfs波形文件的绝对路径
  "OUTPUT": "",			#ASCII波形流文件的存储路径
  "Data Location": "",			#*.wfs文件存储的物理位置，本机对应[PC]，外置硬盘对应[Disk]
  "locations_dialog": {
    "Dir": [],				#StreamToAscii软件输入对话框中的文件路径坐标
    "Search": [],			#StreamToAscii软件输入对话框中的搜索框坐标
    "Search Enter": [],			#StreamToAscii软件输入对话框中的确认搜索坐标
    "Search Result": [],			#StreamToAscii软件输入对话框中的搜索结果坐标
    "Output Name": [],		#StreamToAscii软件输出对话框中的文件路径坐标
    "Screenshot Input File Name": [],	#StreamToAscii软件输入对话框名称坐标（左上角）
    "Screenshot Input Location": [],	#StreamToAscii软件输入对话框中的搜索框坐标（左上角）
    "Screenshot Search": [],		#StreamToAscii软件输入对话框中的搜索结果坐标（左上角）
    "Screenshot Output File Name": [],	#StreamToAscii软件输出对话框名称坐标（左上角）
    "Screenshot Output Location": []	#StreamToAscii软件输出对话框中的搜索框坐标（左上角）
  },
  "locations_software": {	#以下每组坐标配置与软件并行数对应，即同时运行几个软件，下边就有几组坐标配置，这里以2组坐标配置为例
    "locations_center": {
      "WFS": [],				#StreamToAscii软件中WFS坐标
      "Produce ASCII Output File": [],		#StreamToAscii软件中Produce ASCII Output File坐标
      "Show Message Precessing Window": [],	#StreamToAscii软件中Show Message Precessing Window坐标		
      "Convert": [],				#StreamToAscii软件中Convert坐标
      "Input Browse": [],			#StreamToAscii软件中Input Browse坐标
      "Output Browse": [],			#StreamToAscii软件中Output Browse坐标
      "Screenshot": []				#StreamToAscii软件中运行状态坐标
    },
    "locations_centerRight": {
      "WFS": [],
      "Produce ASCII Output File": [],
      "Show Message Precessing Window": [],
      "Convert": [],
      "Input Browse": [],
      "Output Browse": [],
      "Screenshot": []
    }
  }
}
4. [stream.json]中配置模板（#及其后的文字删除）：
{
  "asciiFold": "",		#PAC系统的ASCII波形文件的绝对路径
  "matFold": "",		#Mat波形流文件的存储路径
  "featuresMatFold": "",	#特征Mat波形流文件的存储路径
  "eventFold": "",		#AE事件检测结果的存储路径
  "parallel": 1,		#是否并行，1为是，0为否
  "processor": 2,		#并行数，仅"parallel"为1时有效
  "magnification_dB": 40,	#前放倍数
  "first": 1,			#是否为第一次计算ASCII波形流文件，之后调高ITU只针对先前的计算结果，1为是，0为否
  "staLen": 5,		#短时分析窗口长度，单位μs
  "overlap": 1,		#短时分析窗口重叠量，无量纲
  "staWin": "hamming",	#短时分析窗口函数
  "IZCRT": 0.1,		#阈值自适应算法的初始过零率阈值，仅在"backNoiseTime"为0时有效
  "ITU": 650,		#阈值自适应算法的初始短时能量阈值上限
  "alpha": 1.3,		#阈值自适应算法的背景噪声评估加权因子
  "backNoiseTime": 10000	#阈值自适应算法的背景噪声评估时长，单位μs
}
5. 运行模式[check]：定位当前鼠标位置，用于PAC系统wfs文件自动转换的坐标校验。
6. 运行模式[convert]：用于转换PAC系统*.wfs波形流文件至ASCII波形流文件，每个*.wfs波形流文件只需转换一次，注意储存空间。
7. 运行模式[reconvert]：用于转换ASCII波形流文件至Mat波形流文件，便于提升后续计算效率，每个ASCII波形流文件只需转换一次，注意储存空间。
8. 运行模式[detect]：用于执行阈值自适应算法以检测AE事件，会先读取存储特征的Mat波形流文件，检测到的AE事件存储至配置文件中的保存路径。

II. Statistics
1. 在此脚本目录创建[Statistics.json]
2. [Statistics.json]中配置模板（#及其后的文字删除）：
{
  "features": "Energy",				#Energy、Amplitude、Duration其中之一
  "absolute of file": "C:\\Users\\Yuan\\Desktop\\test.txt",	#目标文件的绝对路径，txt只包含数值
  "save path": "C:\\Users\\Yuan\\Desktop",		#计算结果存储路径
  "interval number": 8,				#计算PDF时每量级的格子数量
  "plot": 0						#是否画图展示，1为是，0为否，若脚本闪退，将此值改为0
}
3. 每次更新[Statistics.json]中的配置后，无需重启脚本
