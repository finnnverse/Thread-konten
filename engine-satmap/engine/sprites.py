import os, cairosvg
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(S,'sprites')
def komodo(body='#7E8F5C',back='#5F6E45',belly='#E3D7A6',line='#2B3320',eye=True,mood='happy',fossil=False,tongue=True):
    if fossil:
        body,back,belly,line='#E9DCC0','#D2C29E','#F3EAD5','#8A7A5C'
    brow=''; extra=''
    if mood=='sad':
        brow=f'<path d="M318 70 L346 78" stroke="{line}" stroke-width="6" stroke-linecap="round"/>'
        extra='<path d="M352 104 q-6 14 0 20 q6 -6 0 -20z" fill="#7FD3FF"/>'
    mouth=f'<path d="M335 118 q22 10 46 -4" stroke="{line}" stroke-width="5" fill="none" stroke-linecap="round"/>' if mood!='sad' else f'<path d="M338 122 q20 -8 42 2" stroke="{line}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    tg=f'<path d="M384 112 l26 4 l10 -8 m-10 8 l10 8" stroke="#FF8A3D" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' if tongue and not fossil else ''
    ey=f'<circle cx="335" cy="88" r="17" fill="#fff" stroke="{line}" stroke-width="4"/><circle cx="340" cy="89" r="8" fill="{line}"/><circle cx="343" cy="85" r="3" fill="#fff"/>' if not fossil else f'<circle cx="335" cy="88" r="13" fill="{line}" opacity=".85"/>'
    cracks=f'<g stroke="{line}" stroke-width="4" fill="none" stroke-linecap="round" opacity=".8"><path d="M150 110 l14 22 l-8 18"/><path d="M230 100 l-10 26 l12 14"/><path d="M290 96 l8 20"/><path d="M90 140 l20 6"/></g>' if fossil else ''
    stripes='' if fossil else f'<g fill="{back}" opacity=".9"><ellipse cx="160" cy="104" rx="16" ry="7"/><ellipse cx="205" cy="98" rx="16" ry="7"/><ellipse cx="250" cy="100" rx="14" ry="6"/><ellipse cx="115" cy="118" rx="13" ry="6"/></g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 230">
<g stroke="{line}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">
<path d="M120 150 C80 160 40 170 14 150 C30 176 80 186 132 170 Z" fill="{body}"/>
<path d="M150 158 l-14 46 h30 l10 -36z" fill="{back}"/>
<path d="M270 158 l-8 46 h30 l6 -40z" fill="{back}"/>
<path d="M110 120 C120 84 220 76 290 86 C320 66 370 66 392 92 C406 108 398 126 372 128 C350 130 330 128 312 138 C290 166 200 176 130 166 C108 162 102 140 110 120 Z" fill="{body}"/>
<path d="M135 158 C190 170 260 166 300 146 C280 168 200 180 130 166z" fill="{belly}" stroke="none"/>
<path d="M200 160 l-12 46 h32 l8 -42z" fill="{body}"/>
<path d="M300 140 l2 66 h30 l-6 -64z" fill="{body}"/>
</g>{stripes}{cracks}{tg}{ey}{brow}{extra}{mouth}
<circle cx="386" cy="96" r="4" fill="{line}"/></svg>'''
CROWN='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 90"><path d="M10 80 L14 22 L40 50 L60 10 L80 50 L106 22 L110 80 Z" fill="#FFC23A" stroke="#7A4B00" stroke-width="6" stroke-linejoin="round"/><circle cx="60" cy="58" r="9" fill="#FF5470"/><circle cx="30" cy="64" r="6" fill="#4ADE80"/><circle cx="90" cy="64" r="6" fill="#5EEAD4"/></svg>'''
TIGER='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 190"><g stroke="#3A2310" stroke-width="7" stroke-linejoin="round">
<circle cx="42" cy="44" r="26" fill="#F08A24"/><circle cx="158" cy="44" r="26" fill="#F08A24"/><circle cx="42" cy="44" r="11" fill="#FFE1C2" stroke="none"/><circle cx="158" cy="44" r="11" fill="#FFE1C2" stroke="none"/>
<ellipse cx="100" cy="104" rx="86" ry="76" fill="#F08A24"/></g>
<g fill="#3A2310"><path d="M100 30 l-10 26 h20z"/><path d="M20 96 l34 8 l-34 12z"/><path d="M180 96 l-34 8 l34 12z"/><path d="M60 40 l10 24 l8 -26z"/><path d="M140 40 l-10 24 l-8 -26z"/></g>
<ellipse cx="100" cy="140" rx="46" ry="32" fill="#FFF3E2"/><circle cx="72" cy="94" r="10" fill="#3A2310"/><circle cx="128" cy="94" r="10" fill="#3A2310"/>
<path d="M60 76 l24 8 M140 76 l-24 8" stroke="#3A2310" stroke-width="7" stroke-linecap="round"/>
<path d="M88 124 h24 l-12 12z" fill="#3A2310"/><path d="M82 150 q18 -10 36 0" stroke="#3A2310" stroke-width="6" fill="none" stroke-linecap="round"/></svg>'''
RESEARCHER='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 420"><g stroke="#23303A" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">
<path d="M80 250 l-6 130 h26 l10 -110 l10 110 h26 l-6 -130z" fill="#3D5A80"/>
<path d="M60 180 q50 -24 100 0 l8 90 h-116z" fill="#2EC4B6"/>
<path d="M78 186 v84 M142 186 v84" stroke="#FFB020" stroke-width="10"/>
<path d="M160 196 l40 -40" fill="none"/><rect x="186" y="128" width="26" height="40" rx="6" fill="#C8A26B" transform="rotate(40 199 148)"/>
<path d="M60 196 l-28 60" fill="none"/>
<circle cx="110" cy="112" r="62" fill="#FFF6EA"/>
<path d="M44 96 q66 -86 132 0 z" fill="#FFB020"/><path d="M36 98 h148" stroke-width="8"/><circle cx="110" cy="62" r="10" fill="#FFF07A"/>
<circle cx="88" cy="120" r="15" fill="#fff"/><circle cx="132" cy="120" r="15" fill="#fff"/><path d="M103 120 h14"/>
</g><circle cx="90" cy="121" r="5" fill="#23303A"/><circle cx="134" cy="121" r="5" fill="#23303A"/>
<path d="M96 150 q14 10 28 0" stroke="#23303A" stroke-width="5" fill="none" stroke-linecap="round"/></svg>'''
FACTORY='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 220"><g stroke="#2B2B36" stroke-width="6" stroke-linejoin="round">
<circle cx="70" cy="40" r="26" fill="#9AA0AE"/><circle cx="104" cy="26" r="20" fill="#B8BDC8"/><circle cx="196" cy="56" r="22" fill="#9AA0AE"/>
<rect x="56" y="70" width="28" height="80" fill="#C94F4F"/><rect x="186" y="90" width="24" height="60" fill="#C94F4F"/>
<path d="M20 210 V140 l60 -30 v30 l60 -30 v30 l60 -30 v100z" fill="#E7E2D6"/>
<rect x="44" y="160" width="26" height="22" fill="#FFC23A"/><rect x="104" y="160" width="26" height="22" fill="#FFC23A"/><rect x="164" y="160" width="26" height="22" fill="#FFC23A"/></g></svg>'''
def save(name,svg,w):
    cairosvg.svg2png(bytestring=svg.encode(),write_to=os.path.join(D,name+'.png'),output_width=w)
if __name__=='__main__':
    os.makedirs(D,exist_ok=True)
    save('komodo',komodo(),700); save('komodo_sad',komodo(mood='sad'),700)
    save('fossil',komodo(fossil=True),700); save('crown',CROWN,240); save('tiger',TIGER,300)
    save('researcher',RESEARCHER,360); save('factory',FACTORY,400)
    from PIL import Image
    ims=[Image.open(os.path.join(D,n+'.png')) for n in ['komodo','komodo_sad','fossil','crown','tiger','researcher','factory']]
    W=sum(i.width for i in ims)+80; H=max(i.height for i in ims)
    sh=Image.new('RGBA',(W,H),(40,60,80,255)); x=0
    for i in ims: sh.alpha_composite(i,(x,0)); x+=i.width+10
    sh.convert('RGB').resize((W//2,H//2)).save(os.path.join(S,'prev_sprites.jpg'))
