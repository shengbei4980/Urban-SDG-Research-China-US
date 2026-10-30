"""Assemble S5 reference composition from the current vector panels without changing scientific marks.

Panel a is the revised geographic display; panel b retains the supplied matrices.
This reference composition does not replace the current document-derived PNG.
Only titles, diagnostic pages and excess margins outside the publication panels
are cropped. Source panel PDFs remain unchanged and independently downloadable.
Requires pypdf, pypdfium2, reportlab and Pillow.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import io
import json
import os

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject
import pypdfium2 as pdfium
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
A = ROOT/'figure_s5a/outputs/Supplementary_Fig_5a_stable_Target_combination_based_institution_city_similarity_reconstructed.pdf'
B = ROOT/'figure_s5b/figures/Supplementary_Fig_5b_all_cities_Target_combinations_clear_label_version.pdf'
OUT = ROOT/'outputs'
QA = ROOT/'review'
# The original two-row, two-country arrangement is retained. Space below the
# maps accommodates the graphical locator leaders without compressing a map.
WIDTH_PT, HEIGHT_PT = 584.88, 529.0
DPI = 600
BLUE, RED = '#003366', '#8B0000'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def add_panel(target, source, crop, x, y, width):
    page=deepcopy(PdfReader(source).pages[0])
    x0,y0,x1,y1=crop
    page.cropbox=RectangleObject(crop)
    page.trimbox=RectangleObject(crop)
    scale=width/(x1-x0)
    transform=Transformation().translate(-x0,-y0).scale(scale).translate(x,y)
    target.merge_transformed_page(page, transform, over=True)
    return {'source':source.relative_to(ROOT).as_posix(), 'source_sha256':sha(source),
            'crop_pdf_points':list(crop), 'placement_pdf_points':[x,y,width,(y1-y0)*scale],
            'isotropic_scale':scale}

def labels_pdf():
    regular,bold='Helvetica','Helvetica-Bold'
    fonts=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    if (fonts/'arial.ttf').is_file() and (fonts/'arialbd.ttf').is_file():
        pdfmetrics.registerFont(TTFont('AssemblyArial',str(fonts/'arial.ttf')))
        pdfmetrics.registerFont(TTFont('AssemblyArialBold',str(fonts/'arialbd.ttf')))
        regular,bold='AssemblyArial','AssemblyArialBold'
    stream=io.BytesIO();c=canvas.Canvas(stream,pagesize=(WIDTH_PT,HEIGHT_PT))
    def text(x,y,value,size=7,color='#202830',weight=False):
        c.setFillColor(color);c.setFont(bold if weight else regular,size);c.drawString(x,y,value)
    text(7,516,'a',11,weight=True)
    text(155,516,'NSF',9,BLUE,True);text(451,516,'NSFC',9,RED,True)
    text(13,291,'Node colour: country',6.2,weight=True)
    for x,color,label in [(92,RED,'NSFC'),(126,BLUE,'NSF')]:
        c.setFillColor(color);c.circle(x,293,2.2,stroke=0,fill=1);text(x+5,291,label,6.2)
    text(205,291,'Edge strength',6.2,weight=True)
    for x,value in [(264,.30),(344,.50),(424,.70)]:
        t=(value-.20)/.60
        alpha=.65+.35*t*t
        # Same fixed scale and 256-entry three-stop ramp as the map renderer.
        lut=min(int(t*256),255)/255
        fraction=lut*2 if lut<=.5 else (lut-.5)*2
        for y,stops in [(295,['#E4EDF5','#7F99B2',BLUE]),(291,['#F6E4E4','#C57F7F',RED])]:
            a,b=stops[:2] if lut<=.5 else stops[1:]
            rgb=lambda h:[int(h[k:k+2],16)/255 for k in (1,3,5)]
            color=[u+(v-u)*fraction for u,v in zip(rgb(a),rgb(b))]
            c.setStrokeColorRGB(*color);c.setStrokeAlpha(alpha)
            c.setLineCap(1);c.setLineWidth((.34+2.35*t**2.10)*574.88/975);c.line(x,y,x+38,y)
        c.setStrokeAlpha(1);text(x+43,291,f'{value:.2f}',6.2)
    text(7,279,'b',11,weight=True)
    # Same four legend meanings and agency hues as the existing complete S3.
    y=4.7
    for x,label,color in [(132,'Observed in NSF',BLUE),(229,'Observed in NSFC',RED),(334,'Not observed',None)]:
        c.setLineWidth(.5);c.setStrokeColor('#A5ADB5');c.setFillColor(color or '#FFFFFF')
        c.rect(x,y-.2,10,4.8,stroke=0 if color else 1,fill=1);text(x+15,y-.3,label,7)
    c.setStrokeColor('#7E8993');c.setLineWidth(.5);c.line(433,y+2,444,y+2)
    text(449,y-.3,'City-profile clustering',7)
    c.showPage();c.save();stream.seek(0);return PdfReader(stream)

def main():
    OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
    writer=PdfWriter();page=writer.add_blank_page(width=WIDTH_PT,height=HEIGHT_PT)
    panels=[]
    panels.append(add_panel(page,A,(20,284,995,638),5,304,574.88))
    # Identical source, matching isotropic scale for the two national matrices.
    panels.append(add_panel(page,B,(76,155,650,725),5,13,260))
    panels.append(add_panel(page,B,(782,155,1356,725),WIDTH_PT-265,13,260))
    page.merge_page(labels_pdf().pages[0])
    pdf=OUT/'Supplementary_Fig_5_source_composition.pdf'
    with pdf.open('wb') as f:writer.write(f)
    document=pdfium.PdfDocument(pdf);bitmap=document[0].render(scale=DPI/72)
    image=bitmap.to_pil().convert('RGB')
    image.save(OUT/'Supplementary_Fig_5_source_composition.png',dpi=(DPI,DPI),optimize=True)
    image.thumbnail((1500,1500));image.save(QA/'composite_preview.png',dpi=(150,150))
    report={'composition_date':'2026-10-11','scientific_marks_changed':False,
            'panel_b_source_unchanged':True,'archetype':'asymmetric mixed-modality figure',
            'conclusion':'Stable Target-combination similarity and city coverage differ between NSF and NSFC.',
            'evidence_chain':{'a':'Institution-city similarity maps with geographic inset locators.',
                              'b':'Full supplied Target-pair matrices and descriptive city-profile clustering.'},
            'backend':'python','raster_dpi':DPI,'page_size_points':[WIDTH_PT,HEIGHT_PT],
            'panels':panels,'contrast_gamma_adjustment':None,'font_text_editable_in_pdf':True,
            'crop_policy':'Publication map/matrix areas retained; source headers and supporting diagnostic pages excluded.',
            'size_note':'Source arrangement retained. The dense city matrices remain available as vector PDFs and separate zoom outputs.',
            'png_sha256':sha(OUT/'Supplementary_Fig_5_source_composition.png'),'pdf_sha256':sha(pdf)}
    (QA/'composition_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pdf':str(pdf),'png':str(OUT/'Supplementary_Fig_5_source_composition.png'),'dpi':DPI}))

if __name__=='__main__':main()
