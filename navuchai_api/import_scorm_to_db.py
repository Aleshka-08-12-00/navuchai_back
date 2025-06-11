import os, re, zipfile, tempfile, shutil, asyncio, json, xml.etree.ElementTree as ET
from pathlib import Path
from app.config import SessionLocal
from app.schemas.course import CourseCreate
from app.schemas.module import ModuleCreate
from app.schemas.lesson import LessonCreate
from app.crud.course import create_course
from app.crud.module import create_module
from app.crud.lesson import create_lesson

def extract_js(path):
    txt = Path(path).read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'"title"\s*:\s*"([^"]+)"', txt)
    title = m.group(1) if m else Path(path).stem
    body = re.search(r'"text"\s*:\s*"([^"]+)"', txt)
    content = body.group(1).encode('utf-8').decode('unicode_escape') if body else txt
    return title, f'<div>{content}</div>'

def extract_xcd(path):
    root = ET.parse(path).getroot()
    title = root.attrib.get('title', Path(path).stem)
    texts = ' '.join(t.text or '' for t in root.findall('.//text'))
    return title, f'<div>{texts}</div>'

async def import_zip(zp, author_id):
    tmp = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(zp) as z:
        z.extractall(tmp)
    imf = tmp/'imsmanifest.xml'
    org = ET.parse(imf).getroot().find('.//{*}organization')
    course_title = org.find('{*}title').text
    async with SessionLocal() as db:
        course = await create_course(db, CourseCreate(title=course_title, description=course_title), author_id)
        module = await create_module(db, ModuleCreate(course_id=course.id, title='Слайды', order=1))
        order = 1
        for f in (tmp/'res'/'data').iterdir():
            if f.suffix.lower() == '.html':
                title = f.stem
                html = f.read_text(encoding='utf-8', errors='ignore')
            elif f.suffix.lower() == '.js':
                title, html = extract_js(f)
            elif f.suffix.lower() == '.xcd':
                title, html = extract_xcd(f)
            else:
                continue
            await create_lesson(db, LessonCreate(module_id=module.id, title=title, content=html, order=order))
            order += 1
    shutil.rmtree(tmp)

async def main():
    author_id = int(os.getenv('DEFAULT_AUTHOR_ID', '2'))
    for z in Path('scorm_zips').glob('*.zip'):
        await import_zip(z, author_id)

if __name__ == '__main__':
    asyncio.run(main())
