from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup as bs
import requests, json, datetime, re, io, base64

app = Flask(__name__)
sKey = 'Lord2333'


@app.route('/', methods=['GET', 'POST'])
def main():
	if sKey:
		if request.headers.get('sKey') != sKey:
			return '当前接口已开启身份验证，请在请求头中添加sKey字段！'
		else:
			if request.method == 'POST':
				try:
					data = json.loads(request.get_data())
					day = data['day']
					Base = data['base64']
					try:
						day.isdigit()
					except AttributeError:
						return 'day字段必须为字符串，形如"0712"'
					if Base:
						return render_pic(get_web(day), Base)
					return data
				except Exception as e:
					return "缺少字段"+str(e)
			else:
				return send_file(render_pic(get_web()), mimetype='image/png')
	else:
		if request.method == 'POST':
			data = json.loads(request.get_data())
			day = data['day']
			return data
		else:
			return send_file(render_pic(get_web()), mimetype='image/png')


headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
font = ImageFont.truetype('./MSYH.TTC', 15, encoding='utf-8')
font_y = ImageFont.truetype('./MSYH.TTC', 13, encoding='utf-8')


def get_web(today: str = datetime.datetime.now().strftime('%m%d')) -> list:
	"""
	从百度百科获取历史上的今天

	:param today: 输入格式为月日，如：'0707'，默认为今天
	:return: 返回传入时间当天的历史事件
	"""
	month = today[:2]
	day = today[2:]
	url = 'https://baike.baidu.com/cms/home/eventsOnHistory/' + month + '.json'
	response = requests.get(url=url, headers=headers).text.encode("utf-8")
	data = json.loads(response)
	data_today = data[month][today]
	data_today.reverse()
	return data_today


def render_pic(Data: list, Base64: bool = False):
	Font = ImageFont.truetype('./MSYH.TTC', 28, encoding='utf-8')
	mask_img = Image.open('./mask.png').convert("RGBA")
	mask_img = mask_img.resize((128, 192))
	high = (int(round(len(Data)/3, 0)))*210+146  # 计算最终图片高度，图片上下间距18
	img_event = Image.new('RGB', (444, high), (255, 255, 255))  # 444 = 128*3+15*4 图片左右间距15
	img_pai = Image.open('./Patrick.jpg')
	count = 0
	X = 15
	Y = 18
	for event in Data:
		url = event['link']
		res = requests.get(url=url, headers=headers)
		soup = bs(res.text, 'html.parser')
		tittle = re.sub(r"<(\S*?)[^>]*>.*?|<.*? />", '', event['title'])
		try:
			pic = soup.find('div', class_='summary-pic')
			pic_url = pic.find('img')['src']
			size_rule = r',[a-zA-Z0-9\w,]*,'
			cen_rule = r'\?'
			pic_url = re.sub(size_rule, ',m_fill,w_128,h_128,align_0,', pic_url).replace('pic', 'smart')
			pic_url = re.sub(cen_rule, '-bkimg-process,v_1,rw_1,rh_1,maxl_800,pad_1?', pic_url)
			single_pic = render_single(pic_url, tittle, event['year'], mask_img)
		except AttributeError:
			pic_url = ""
			single_pic = render_single(pic_url, tittle, event['year'], mask_img)
		if count % 3 == 0 and count != 0:
			X = 15
			Y += 210
		count += 1
		img_event.paste(single_pic, (X, Y))
		del single_pic
		X += 143
	X = 15
	Y += 210
	img_event.paste(img_pai, (X, Y))
	draw = ImageDraw.Draw(img_event)
	draw.multiline_text((X+128+10, Y+20), 'API By\nGithub@Lord2333', font=Font, fill=(0, 0, 0), align='center')
	temp = io.BytesIO()
	img_event.save(temp, format='png')
	temp.seek(0)
	if Base64:
		base64_str = base64.b64encode(temp.getvalue()).decode('utf-8')
		return base64_str
	return temp


def render_single(url: str, desc: str, year: str, mask_img: Image.Image) -> Image.Image:
	# 使用pillow绘制圆角矩形图片，格式为RGBA，大小为128*192
	im = Image.new('RGBA', (128, 192), (255, 255, 255, 0))  # 创建透明底图
	im_text = Image.new('RGB', (128, 64), (208, 208, 208))  # 创建文字底图
	img_year = Image.open('./year.png').convert("RGBA")
	img_year = img_year.resize((55, 18))
	space = 10  # 文字与图片的间距
	if url:
		response = requests.get(url, headers=headers)
		img = Image.open(io.BytesIO(response.content))
		im.paste(img, (0, 0))
	else:
		nopic = Image.open('./nopic.jpg')
		im.paste(nopic, (0, 0))
	if desc:
		if len(desc) > 14:
			desc = desc[:14] + '...'
		desc = desc[:7] + '\n' + desc[7:]
		draw = ImageDraw.Draw(im_text, 'RGBA')
		draw.multiline_text((space, space), desc, fill=(0, 0, 0, 1), font=font)
		del draw
		im.paste(im_text, (0, 128))
	draw = ImageDraw.Draw(img_year, 'RGBA')
	draw.text((5, 1), year + "年", fill=(255, 255, 255), font=font_y)
	_, _, _, a1 = img_year.split()
	_, _, _, a2 = mask_img.split()
	im.paste(img_year, (5, 5), mask=a1)
	im.paste(mask_img, (0, 0), mask=a2)
	del draw
	return im


def simplify_data(Data: list) -> list:
	Event = []
	for event in Data:
		year = event['year']
		tittle = re.sub(r"<(\S*?)[^>]*>.*?|<.*? />", '', event['title'])
		desc = re.sub(r"<(\S*?)[^>]*>.*?|<.*? />", '', event['desc'])
		Event.append(year + '年：' + tittle + '\n' + desc)
	# print(Event)
	return Event
