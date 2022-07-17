import subprocess
import glob
import sys
import re
import os

debug = 0
same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
DEFAULT_TXT = os.path.join(same_hierarchy,'default.txt')
MJDISASM_EXE = os.path.join(same_hierarchy,'mjdisasm.exe')

if debug:
	same_hierarchy = os.path.join(same_hierarchy,'Tiger_Musuhira_EXT')#debug

DIR_ARC = os.path.join(same_hierarchy,'arc')

effect_startnum = 10
effect_list = []
gosub_list = []
mjo_list = [#ここに変換するmjoの名前を書く
	'prologue',
]


d = {}


def text_dec():
	for p in glob.glob(os.path.join(DIR_ARC, '*.mjo')):
		name = os.path.splitext(os.path.basename(p))[0]
		b = False
		for s in mjo_list:
			if name == s:
				b = True

		if b:
			subprocess.run([MJDISASM_EXE, p], shell=True, cwd=DIR_ARC)


def effect_edit(t,f):
	global effect_list

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list) + effect_startnum

	return str(list_num)


def text_cnv():
	global gosub_list

	with open(DEFAULT_TXT) as f:
		txt = f.read()

	for i,p in enumerate( glob.glob(os.path.join(DIR_ARC, '*.mjs')) ):
		name = os.path.splitext(os.path.basename(p))[0]
		txt += '\n;--------------- '+ name +' ---------------\n*SCR_'+ name.replace('.', '_') +'\n\n'
		p2 = os.path.splitext(p)[0] + '.sjs'

		if os.path.exists(p2):
			with open(p2, encoding='cp932', errors='ignore') as f:
				for line in f:
					search_line = re.search(r'\<([0-9]+?)\> (.+?)\n', line)
					d[str(i)+'_'+search_line[1]] = search_line[2]

		with open(p, encoding='cp932', errors='ignore') as f:
			for line in f:
				res_line = re.match(r'\#res<([0-9]+?)>', line)
				nvl_line = re.match(r'call<\$35395c9f,[\t\s]*([0-9])>[\t\s]*\(([0-9])\)', line)
				bg_line = re.match(r'call<\$a4eb1e4c,[\t\s]*([0-9])>[\t\s]*\(\'(.*?)\',[\t\s]*\-?([0-9]*)\)', line)
				tati_line = re.match(r'call<\$dde10ff9,[\t\s]*0>[\t\s]*\(\'(.*?)\'(,[\t\s]*(-?[0-9]))?\)', line)
				push_res_line = re.match(r'push[\t\s]*\#res<([0-9]+?)>', line)
				jne_line = re.match(r'jne[\t\s]*\(([0-9]+?)\)[\t\s]*@([0-9]+)', line)
				goto_line = re.match(r'goto[\t\s]+?@([0-9]+)', line)
				at_line = re.match(r'[\t\s]+?@([0-9]+)', line)
				vo_line = re.match(r'call<\$812afdf0,[\t\s]*[0-9]>[\t\s]*\(\'(.*?)\'\)', line)
				se_line = re.match(r'syscall<\$f62e3ca7>[\t\s]*\(\'(.*?)\'(,[\t\s]*[0-9])?\)', line)
				se2_line = re.match(r'syscall<\$90d5298a>[\t\s]*\(\'(.*?)\'(,[\t\s]*[0-9])?\)', line)
				bgm_line = re.match(r'syscall<\$4980f82c>[\t\s]*\(\'(.*?)\'(,[\t\s]*[0-9])?\)', line)
				fade_line = re.match(r'syscall<\$379fdb39>[\t\s]*\(([0-9]+?)\)', line)
				wait_line = re.match(r'syscall<\$15eedeaa>[\t\s]*\(([0-9]+?)\)', line)
				quake_line = re.match(r'call<\$e9d62d7b,[\t\s]*[0-9]>[\t\s]*\(([0-9]+?)\)', line)

				if res_line:
					line_tmp = str(d[ str(i)+'_'+res_line[1] ]).replace('\\n', '\n') + '\n'#↑と結合処理
					mes_line = re.match(r'(.+?)(（.+?）)?「([^A-z0-9-_]+)', line_tmp)

					if mes_line:
						line = 'name "' + mes_line[1] + '"\n「' + mes_line[3] + '\n'

					else:
						line = line_tmp

				elif tati_line:
					if tati_line[3] == None:
						tati_line_3_ = '5'
					elif tati_line[3] == '-1':						
						tati_line_3_ = '10'
					else:
						tati_line_3_ = str(int(tati_line[3]))

					line = 'tati "' + tati_line[1] + '",' + tati_line_3_ + '\n'

				elif nvl_line:
					line = 'def_adv2nvl ' + nvl_line[1] + ',' + nvl_line[2] + '\n'

				elif bg_line:
					line = 'taticsp:bg "arc\\' + bg_line[2] + '.png",' + effect_edit(bg_line[3], 'fade') + ':mov %11,1\n'
				
				elif push_res_line:
					line = 'select_set "' + str(d[ str(i)+'_'+push_res_line[1] ]) + '"\n'

				elif jne_line:
					#"%40>選択肢"ってどんな命令だよ...(愚痴)
					line = 'select_start:if %40>' + jne_line[1] + ' goto *SCR_'+ name.replace('.', '_') + '_' + jne_line[2] + '\n'

				elif goto_line:
					line = 'goto *SCR_'+ name.replace('.', '_') + '_' + goto_line[1] + '\n'

				elif at_line:
					line = '*SCR_'+ name.replace('.', '_') + '_' + at_line[1] + '\n'
				
				elif vo_line:
					line = 'def_se 0,"' + vo_line[1] + '"\n'

				elif se_line:
					line = 'def_se 1,"' + se_line[1] + '"\n'

				elif se2_line:
					line = 'def_se 2,"' + se2_line[1] + '"\n'

				elif bgm_line:
					line = 'def_bgm "' + bgm_line[1] + '"\n'

				elif fade_line:
					line = 'stopfadeout ' + fade_line[1] + '\n'

				elif wait_line:
					line = 'wait ' + wait_line[1] + '\n'

				elif quake_line:
					line = 'quake 5,'+ quake_line[1] + '*100\n'



				elif re.match(r'syscall<\$0c070535>', line):
					line = 'stop\n'

				elif re.match(r'text_control', line):
					line = '<<TXT_CTL>>'

				elif re.match(r'exit[\t\s]+?', line):
					line = 'csp -1:reset\n'

				elif re.match(r'push', line):
					line = ''

				elif re.match(r'op[A-z0-9]{3}', line):
					line = ''

				elif re.search(r'pause\n', line):
					pass

				elif re.search(r'cls\n', line):
					pass

				elif re.match(r'call<\$5f271e74,', line):
					line = 'def_print\n'

				elif re.match(r'syscall<$f8004993>', line):
					line = ';' + line

				elif re.match(r'syscall<\$f8004993>[\t\s]*\(#res', line):
					line = 'stop\n'

				elif re.match(r'call<\$0a4e49ab,[\t\s]*', line):
					line = 'click\n'


				
				else:
					line = ';' + line

					if debug:
						print(line[:-1])

				txt += line
			
			txt += '\nerrmsg:reset\n'

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換
		if e[1] == 'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'

	#ルビチェック時のみコメントアウト推奨
	txt = txt.replace('\n<<TXT_CTL>>', '')
	txt = txt.replace('<<TXT_CTL>>', '')

	#ルビ置換 例:(今日/きょう)はとても(良/よ)い(天気/てんき)です。 - 正直自動化したかった
	if not debug:
		txt = txt.replace(r'おやしろさま御社様', r'(御社様/おやしろさま)')
		txt = txt.replace(r'しのはらこうた篠原孝太', r'(篠原孝太/しのはらこうた)')
		txt = txt.replace(r'こいずみよしの小泉芳乃', r'(小泉芳乃/こいずみよしの)')
		txt = txt.replace(r'せ　と　うち瀬戸内', r'(瀬戸内/せ　と　うち)')
		txt = txt.replace(r'へきえき辟易している。', r'(辟易/へきえき)している。')
		txt = txt.replace(r'　ザ　ッ　トｔｈａｔ？」', r'(ｔｈａｔ/　ザ　ッ　ト)？」')
		txt = txt.replace(r'ろうらく篭絡していたのが功を奏したか。', r'(篭絡/ろうらく)していたのが功を奏したか。')


	txt = txt.replace('pause\ncls\n', 'cls\n')#pause→clsだとクリック二回必要じゃん？それ修正
	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)
	open(os.path.join(same_hierarchy,'0.txt'), 'w', errors='ignore').write(txt)


def file_check():
	c = True
	for p in [DIR_ARC, DEFAULT_TXT]:
		if not os.path.exists(p):
			print(p+ ' is not found!')
			c = False
	
	return c


def junk_del():
	pass
	#削除予定
	#mjo cfg env mjs sjs


if file_check():
	text_dec()
	text_cnv()


##### memo #####
# call<$a4eb1e4c, 0> ('black', 800) 背景
# pause ￥
# cls  開始前みたいな
# 35395c9f ADV/NVL MODE切り替え？

#;call<$dde10ff9, 0> ('matu_a_a_12')		通常立ち絵
#;call<$dde10ff9, 0> ('matu_a_b_09', 1)		右立ち絵
#;call<$dde10ff9, 0> ('yosi_a_b_08', 2)		左立ち絵
#;call<$dde10ff9, 0> ('', -1)				立ち絵消去


#なにこれ～
#call<$84779a85, 0> (syscall<$924ee3eb>(0, 1, 1), syscall<$924ee3eb>(255, 255, 255), 220)
#call<$84779a85, 0> (syscall<$924ee3eb>(0, 1, 1), syscall<$924ee3eb>(255, 255, 255), 220)
