"""Content-aware SVG visual generation for AcaciaFund blog posts.

Generates dynamic, topic-derived visuals for blog cards, OG images,
and in-post data bars — replacing static category-only thumbnails.
"""

import hashlib
import math
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.brand import BRAND, PILLAR_MAP, _brand_key

STATIC_DIR = Path(__file__).parent.parent / "static" / "images"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Canonical brand palettes — sourced from core/brand.py
PILLAR_PALETTES = {
    "aml":     {"primary": BRAND["aml"]["dark"],     "secondary": "#2d5a8e", "accent": BRAND["aml"]["secondary"],     "bg": BRAND["aml"]["darker"]},
    "stock":   {"primary": BRAND["markets"]["dark"],  "secondary": "#15803d", "accent": BRAND["markets"]["secondary"], "bg": BRAND["markets"]["darker"]},
    "science": {"primary": BRAND["science"]["dark"],  "secondary": "#a855f7", "accent": BRAND["science"]["secondary"], "bg": BRAND["science"]["darker"]},
}

TOPIC_ICONS = {
    # AML
    "regulation":     '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>',
    "compliance":     '<rect fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" x="3" y="3" width="18" height="18" rx="2"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4"/>',
    "crypto":         '<circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="10"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6v12M9 9h6l-3 6-3-6z"/>',
    "fraud":          '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="3"/>',
    "banking":        '<rect fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" x="2" y="8" width="20" height="14" rx="2"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2L2 8h20L12 2z"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 14v4M12 14v4M16 14v4"/>',
    # Markets
    "semiconductor":  '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6 6h12v12H6z"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 8h8v8H8z"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 10h4v4h-4z"/>',
    "ai":             '<circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="10"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v8M8 12h8"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="3"/>',
    "stock_market":   '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2 20h20M6 16l4-4 4 4 4-8"/>',
    "startup":        '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2L2 7l10 5 10-5-10-5z"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2 17l10 5 10-5"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 22V12"/>',
    "manufacturing":  '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 4h16v16H4z"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="4"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v8M8 12h8"/>',
    # Science
    "dna":            '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 2c0 0 0 20 8 20M16 2c0 0 0 20-8 20M8 12h8"/>',
    "quantum":        '<circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="3"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="16" cy="8" r="1.5"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="16" cy="16" r="1.5"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="8" cy="8" r="1.5"/><circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="8" cy="16" r="1.5"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 3v2M12 19v2M3 12h2M19 12h2"/>',
    "brain":          '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2C8 2 4 5 4 10c0 3 2 5 2 5s0 5 6 5 6-5 6-5 2-2 2-5c0-5-4-8-8-8z"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 10h6M10.5 12h3M10 8h4"/>',
    "space":          '<circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="10"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2 12h20M12 2a16 16 0 010 20 16 16 0 010-20z"/><ellipse fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" rx="4" ry="10"/>',
    "climate":        '<circle fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" cx="12" cy="12" r="10"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2a8 8 0 000 16"/><path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 6l2 2M16 6l-2 2"/>',
    # Tech brands (Simple Icons — filled, use currentColor)
    "kafka":          '<path fill="currentColor" d="M9.71 2.136a1.43 1.43 0 0 0-2.047 0h-.007a1.48 1.48 0 0 0-.421 1.042c0 .41.161.777.422 1.039l.007.007c.257.264.616.426 1.019.426.404 0 .766-.162 1.027-.426l.003-.007c.261-.262.421-.629.421-1.039 0-.408-.159-.777-.421-1.042H9.71zM8.683 22.295c.404 0 .766-.167 1.027-.429l.003-.008c.261-.261.421-.631.421-1.036 0-.41-.159-.778-.421-1.044H9.71a1.42 1.42 0 0 0-1.027-.432 1.4 1.4 0 0 0-1.02.432h-.007c-.26.266-.422.634-.422 1.044 0 .406.161.775.422 1.036l.007.008c.258.262.617.429 1.02.429zm7.89-4.462c.359-.096.683-.33.882-.684l.027-.052a1.47 1.47 0 0 0 .114-1.067 1.454 1.454 0 0 0-.675-.896l-.021-.014a1.425 1.425 0 0 0-1.078-.132c-.36.091-.684.335-.881.686-.2.349-.241.75-.146 1.119.099.363.33.691.675.896h.002c.346.203.737.239 1.101.144zm-6.405-7.342a2.083 2.083 0 0 0-1.485-.627c-.58 0-1.103.242-1.482.627-.378.385-.612.916-.612 1.507s.233 1.124.612 1.514a2.08 2.08 0 0 0 2.967 0c.379-.39.612-.923.612-1.514s-.233-1.122-.612-1.507zm-.835-2.51c.843.141 1.6.552 2.178 1.144h.004c.092.093.182.196.265.299l1.446-.851a3.176 3.176 0 0 1-.047-1.808 3.149 3.149 0 0 1 1.456-1.926l.025-.016a3.062 3.062 0 0 1 2.345-.306c.77.21 1.465.721 1.898 1.482v.002c.431.757.518 1.626.313 2.408a3.145 3.145 0 0 1-1.456 1.928l-.198.118h-.02a3.095 3.095 0 0 1-2.154.201 3.127 3.127 0 0 1-1.514-.944l-1.444.848a4.162 4.162 0 0 1 0 2.879l1.444.846c.413-.47.939-.789 1.514-.944a3.041 3.041 0 0 1 2.371.319l.048.023v.002a3.17 3.17 0 0 1 1.408 1.906 3.215 3.215 0 0 1-.313 2.405l-.026.053-.003-.005a3.147 3.147 0 0 1-1.867 1.436 3.096 3.096 0 0 1-2.371-.318v-.006a3.156 3.156 0 0 1-1.456-1.927 3.175 3.175 0 0 1 .047-1.805l-1.446-.848a3.905 3.905 0 0 1-.265.294l-.004.005a3.938 3.938 0 0 1-2.178 1.138v1.699a3.09 3.09 0 0 1 1.56.862l.002.004c.565.572.914 1.368.914 2.243 0 .873-.35 1.664-.914 2.239l-.002.009a3.1 3.1 0 0 1-2.21.931 3.1 3.1 0 0 1-2.206-.93h-.002v-.009a3.186 3.186 0 0 1-.916-2.239c0-.875.35-1.672.916-2.243v-.004h.002a3.1 3.1 0 0 1 1.558-.862v-1.699a3.926 3.926 0 0 1-2.176-1.138l-.006-.005a4.098 4.098 0 0 1-1.173-2.874c0-1.122.452-2.136 1.173-2.872h.006a3.947 3.947 0 0 1 2.176-1.144V6.289a3.137 3.137 0 0 1-1.558-.864h-.002v-.004a3.192 3.192 0 0 1-.916-2.243c0-.871.35-1.669.916-2.243l.002-.002A3.084 3.084 0 0 1 8.683 0c.861 0 1.641.355 2.21.932v.002h.002c.565.574.914 1.372.914 2.243 0 .876-.35 1.667-.914 2.243l-.002.005a3.142 3.142 0 0 1-1.56.864v1.692zm8.121-1.129l-.012-.019a1.452 1.452 0 0 0-.87-.668 1.43 1.43 0 0 0-1.103.146h.002c-.347.2-.58.529-.677.896-.095.365-.054.768.146 1.119l.007.009c.2.347.519.579.874.673.357.103.755.059 1.098-.144l.019-.009a1.47 1.47 0 0 0 .657-.885 1.493 1.493 0 0 0-.141-1.118"/>',
    "kubernetes":     '<path fill="currentColor" d="M10.204 14.35l.007.01-.999 2.413a5.171 5.171 0 0 1-2.075-2.597l2.578-.437.004.005a.44.44 0 0 1 .484.606zm-.833-2.129a.44.44 0 0 0 .173-.756l.002-.011L7.585 9.7a5.143 5.143 0 0 0-.73 3.255l2.514-.725.002-.009zm1.145-1.98a.44.44 0 0 0 .699-.337l.01-.005.15-2.62a5.144 5.144 0 0 0-3.01 1.442l2.147 1.523.004-.002zm.76 2.75l.723.349.722-.347.18-.78-.5-.623h-.804l-.5.623.179.779zm1.5-3.095a.44.44 0 0 0 .7.336l.008.003 2.134-1.513a5.188 5.188 0 0 0-2.992-1.442l.148 2.615.002.001zm10.876 5.97l-5.773 7.181a1.6 1.6 0 0 1-1.248.594l-9.261.003a1.6 1.6 0 0 1-1.247-.596l-5.776-7.18a1.583 1.583 0 0 1-.307-1.34L2.1 5.573c.108-.47.425-.864.863-1.073L11.305.513a1.606 1.606 0 0 1 1.385 0l8.345 3.985c.438.209.755.604.863 1.073l2.062 8.955c.108.47-.005.963-.308 1.34zm-3.289-2.057c-.042-.01-.103-.026-.145-.034-.174-.033-.315-.025-.479-.038-.35-.037-.638-.067-.895-.148-.105-.04-.18-.165-.216-.216l-.201-.059a6.45 6.45 0 0 0-.105-2.332 6.465 6.465 0 0 0-.936-2.163c.052-.047.15-.133.177-.159.008-.09.001-.183.094-.282.197-.185.444-.338.743-.522.142-.084.273-.137.415-.242.032-.024.076-.062.11-.089.24-.191.295-.52.123-.736-.172-.216-.506-.236-.745-.045-.034.027-.08.062-.111.088-.134.116-.217.23-.33.35-.246.25-.45.458-.673.609-.097.056-.239.037-.303.033l-.19.135a6.545 6.545 0 0 0-4.146-2.003l-.012-.223c-.065-.062-.143-.115-.163-.25-.022-.268.015-.557.057-.905.023-.163.061-.298.068-.475.001-.04-.001-.099-.001-.142 0-.306-.224-.555-.5-.555-.275 0-.499.249-.499.555l.001.014c0 .041-.002.092 0 .128.006.177.044.312.067.475.042.348.078.637.056.906a.545.545 0 0 1-.162.258l-.012.211a6.424 6.424 0 0 0-4.166 2.003 8.373 8.373 0 0 1-.18-.128c-.09.012-.18.04-.297-.029-.223-.15-.427-.358-.673-.608-.113-.12-.195-.234-.329-.349-.03-.026-.077-.062-.111-.088a.594.594 0 0 0-.348-.132.481.481 0 0 0-.398.176c-.172.216-.117.546.123.737l.007.005.104.083c.142.105.272.159.414.242.299.185.546.338.743.522.076.082.09.226.1.288l.16.143a6.462 6.462 0 0 0-1.02 4.506l-.208.06c-.055.072-.133.184-.215.217-.257.081-.546.11-.895.147-.164.014-.305.006-.48.039-.037.007-.09.02-.133.03l-.004.002-.007.002c-.295.071-.484.342-.423.608.061.267.349.429.645.365l.007-.001.01-.003.129-.029c.17-.046.294-.113.448-.172.33-.118.604-.217.87-.256.112-.009.23.069.288.101l.217-.037a6.5 6.5 0 0 0 2.88 3.596l-.09.218c.033.084.069.199.044.282-.097.252-.263.517-.452.813-.091.136-.185.242-.268.399-.02.037-.045.095-.064.134-.128.275-.034.591.213.71.248.12.556-.007.69-.282v-.002c.02-.039.046-.09.062-.127.07-.162.094-.301.144-.458.132-.332.205-.68.387-.897.05-.06.13-.082.215-.105l.113-.205a6.453 6.453 0 0 0 4.609.012l.106.192c.086.028.18.042.256.155.136.232.229.507.342.84.05.156.074.295.145.457.016.037.043.09.062.129.133.276.442.402.69.282.247-.118.341-.435.213-.71-.02-.039-.045-.096-.065-.134-.083-.156-.177-.261-.268-.398-.19-.296-.346-.541-.443-.793-.04-.13.007-.21.038-.294-.018-.022-.059-.144-.083-.202a6.499 6.499 0 0 0 2.88-3.622c.064.01.176.03.213.038.075-.05.144-.114.28-.104.266.039.54.138.87.256.154.06.277.128.448.173.036.01.088.019.13.028l.009.003.007.001c.297.064.584-.098.645-.365.06-.266-.128-.537-.423-.608zM16.4 9.701l-1.95 1.746v.005a.44.44 0 0 0 .173.757l.003.01 2.526.728a5.199 5.199 0 0 0-.108-1.674A5.208 5.208 0 0 0 16.4 9.7zm-4.013 5.325a.437.437 0 0 0-.404-.232.44.44 0 0 0-.372.233h-.002l-1.268 2.292a5.164 5.164 0 0 0 3.326.003l-1.27-2.296h-.01zm1.888-1.293a.44.44 0 0 0-.27.036.44.44 0 0 0-.214.572l-.003.004 1.01 2.438a5.15 5.15 0 0 0 2.081-2.615l-2.6-.44-.004.005z"/>',
    "terraform":      '<path fill="currentColor" d="M1.44 0v7.575l6.561 3.79V3.787zm21.12 4.227l-6.561 3.791v7.574l6.56-3.787zM8.72 4.23v7.575l6.561 3.787V8.018zm0 8.405v7.575L15.28 24v-7.578z"/>',
    "docker":         '<path fill="currentColor" d="M13.983 11.078h2.119a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.119a.185.185 0 0 0-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 0 0 .186-.186V3.574a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 0 0 .186-.186V6.29a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 0 0 .184-.186V6.29a.185.185 0 0 0-.185-.185H8.1a.185.185 0 0 0-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 0 0 .185-.186V6.29a.185.185 0 0 0-.185-.185H5.136a.186.186 0 0 0-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 0 0 .185-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.186.186 0 0 0-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 0 0-.75.748 11.376 11.376 0 0 0 .692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 0 0 3.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/>',
    "python":         '<path fill="currentColor" d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"/>',
    "postgresql":     '<path fill="currentColor" d="M23.5594 14.7228a.5269.5269 0 0 0-.0563-.1191c-.139-.2632-.4768-.3418-1.0074-.2321-1.6533.3411-2.2935.1312-2.5256-.0191 1.342-2.0482 2.445-4.522 3.0411-6.8297.2714-1.0507.7982-3.5237.1222-4.7316a1.5641 1.5641 0 0 0-.1509-.235C21.6931.9086 19.8007.0248 17.5099.0005c-1.4947-.0158-2.7705.3461-3.1161.4794a9.449 9.449 0 0 0-.5159-.0816 8.044 8.044 0 0 0-1.3114-.1278c-1.1822-.0184-2.2038.2642-3.0498.8406-.8573-.3211-4.7888-1.645-7.2219.0788C.9359 2.1526.3086 3.8733.4302 6.3043c.0409.818.5069 3.334 1.2423 5.7436.4598 1.5065.9387 2.7019 1.4334 3.582.553.9942 1.1259 1.5933 1.7143 1.7895.4474.1491 1.1327.1441 1.8581-.7279.8012-.9635 1.5903-1.8258 1.9446-2.2069.4351.2355.9064.3625 1.39.3772a.0569.0569 0 0 0 .0004.0041 11.0312 11.0312 0 0 0-.2472.3054c-.3389.4302-.4094.5197-1.5002.7443-.3102.064-1.1344.2339-1.1464.8115-.0025.1224.0329.2309.0919.3268.2269.4231.9216.6097 1.015.6331 1.3345.3335 2.5044.092 3.3714-.6787-.017 2.231.0775 4.4174.3454 5.0874.2212.5529.7618 1.9045 2.4692 1.9043.2505 0 .5263-.0291.8296-.0941 1.7819-.3821 2.5557-1.1696 2.855-2.9059.1503-.8707.4016-2.8753.5388-4.1012.0169-.0703.0357-.1207.057-.1362.0007-.0005.0697-.0471.4272.0307a.3673.3673 0 0 0 .0443.0068l.2539.0223.0149.001c.8468.0384 1.9114-.1426 2.5312-.4308.6438-.2988 1.8057-1.0323 1.5951-1.6698zM2.371 11.8765c-.7435-2.4358-1.1779-4.8851-1.2123-5.5719-.1086-2.1714.4171-3.6829 1.5623-4.4927 1.8367-1.2986 4.8398-.5408 6.108-.13-.0032.0032-.0066.0061-.0098.0094-2.0238 2.044-1.9758 5.536-1.9708 5.7495-.0002.0823.0066.1989.0162.3593.0348.5873.0996 1.6804-.0735 2.9184-.1609 1.1504.1937 2.2764.9728 3.0892.0806.0841.1648.1631.2518.2374-.3468.3714-1.1004 1.1926-1.9025 2.1576-.5677.6825-.9597.5517-1.0886.5087-.3919-.1307-.813-.5871-1.2381-1.3223-.4796-.839-.9635-2.0317-1.4155-3.5126zm6.0072 5.0871c-.1711-.0428-.3271-.1132-.4322-.1772.0889-.0394.2374-.0902.4833-.1409 1.2833-.2641 1.4815-.4506 1.9143-1.0002.0992-.126.2116-.2687.3673-.4426a.3549.3549 0 0 0 .0737-.1298c.1708-.1513.2724-.1099.4369-.0417.156.0646.3078.26.3695.4752.0291.1016.0619.2945-.0452.4444-.9043 1.2658-2.2216 1.2494-3.1676 1.0128zm2.094-3.988-.0525.141c-.133.3566-.2567.6881-.3334 1.003-.6674-.0021-1.3168-.2872-1.8105-.8024-.6279-.6551-.9131-1.5664-.7825-2.5004.1828-1.3079.1153-2.4468.079-3.0586-.005-.0857-.0095-.1607-.0122-.2199.2957-.2621 1.6659-.9962 2.6429-.7724.4459.1022.7176.4057.8305.928.5846 2.7038.0774 3.8307-.3302 4.7363-.084.1866-.1633.3629-.2311.5454zm7.3637 4.5725c-.0169.1768-.0358.376-.0618.5959l-.146.4383a.3547.3547 0 0 0-.0182.1077c-.0059.4747-.054.6489-.115.8693-.0634.2292-.1353.4891-.1794 1.0575-.11 1.4143-.8782 2.2267-2.4172 2.5565-1.5155.3251-1.7843-.4968-2.0212-1.2217a6.5824 6.5824 0 0 0-.0769-.2266c-.2154-.5858-.1911-1.4119-.1574-2.5551.0165-.5612-.0249-1.9013-.3302-2.6462.0044-.2932.0106-.5909.019-.8918a.3529.3529 0 0 0-.0153-.1126 1.4927 1.4927 0 0 0-.0439-.208c-.1226-.4283-.4213-.7866-.7797-.9351-.1424-.059-.4038-.1672-.7178-.0869.067-.276.1831-.5875.309-.9249l.0529-.142c.0595-.16.134-.3257.213-.5012.4265-.9476 1.0106-2.2453.3766-5.1772-.2374-1.0981-1.0304-1.6343-2.2324-1.5098-.7207.0746-1.3799.3654-1.7088.5321a5.6716 5.6716 0 0 0-.1958.1041c.0918-1.1064.4386-3.1741 1.7357-4.4823a4.0306 4.0306 0 0 1 .3033-.276.3532.3532 0 0 0 .1447-.0644c.7524-.5706 1.6945-.8506 2.802-.8325.4091.0067.8017.0339 1.1742.081 1.939.3544 3.2439 1.4468 4.0359 2.3827.8143.9623 1.2552 1.9315 1.4312 2.4543-1.3232-.1346-2.2234.1268-2.6797.779-.9926 1.4189.543 4.1729 1.2811 5.4964.1353.2426.2522.4522.2889.5413.2403.5825.5515.9713.7787 1.2552.0696.087.1372.1714.1885.245-.4008.1155-1.1208.3825-1.0552 1.717-.0123.1563-.0423.4469-.0834.8148-.0461.2077-.0702.4603-.0994.7662zm.8905-1.6211c-.0405-.8316.2691-.9185.5967-1.0105a2.8566 2.8566 0 0 0 .135-.0406 1.202 1.202 0 0 0 .1342.103c.5703.3765 1.5823.4213 3.0068.1344-.2016.1769-.5189.3994-.9533.6011-.4098.1903-1.0957.333-1.7473.3636-.7197.0336-1.0859-.0807-1.1721-.151zm.5695-9.2712c-.0059.3508-.0542.6692-.1054 1.0017-.055.3576-.112.7274-.1264 1.1762-.0142.4368.0404.8909.0932 1.3301.1066.887.216 1.8003-.2075 2.7014a3.5272 3.5272 0 0 1-.1876-.3856c-.0527-.1276-.1669-.3326-.3251-.6162-.6156-1.1041-2.0574-3.6896-1.3193-4.7446.3795-.5427 1.3408-.5661 2.1781-.463zm.2284 7.0137a12.3762 12.3762 0 0 0-.0853-.1074l-.0355-.0444c.7262-1.1995.5842-2.3862.4578-3.4385-.0519-.4318-.1009-.8396-.0885-1.2226.0129-.4061.0666-.7543.1185-1.0911.0639-.415.1288-.8443.1109-1.3505.0134-.0531.0188-.1158.0118-.1902-.0457-.4855-.5999-1.938-1.7294-3.253-.6076-.7073-1.4896-1.4972-2.6889-2.0395.5251-.1066 1.2328-.2035 2.0244-.1859 2.0515.0456 3.6746.8135 4.8242 2.2824a.908.908 0 0 1 .0667.1002c.7231 1.3556-.2762 6.2751-2.9867 10.5405zm-8.8166-6.1162c-.025.1794-.3089.4225-.6211.4225a.5821.5821 0 0 1-.0809-.0056c-.1873-.026-.3765-.144-.5059-.3156-.0458-.0605-.1203-.178-.1055-.2844.0055-.0401.0261-.0985.0925-.1488.1182-.0894.3518-.1226.6096-.0867.3163.0441.6426.1938.6113.4186zm7.9305-.4114c.0111.0792-.049.201-.1531.3102-.0683.0717-.212.1961-.4079.2232a.5456.5456 0 0 1-.075.0052c-.2935 0-.5414-.2344-.5607-.3717-.024-.1765.2641-.3106.5611-.352.297-.0414.6111.0088.6356.1851z"/>',
    "snowflake":      '<path fill="currentColor" d="M24 3.459c0 .646-.418 1.18-1.141 1.18-.723 0-1.142-.534-1.142-1.18 0-.647.419-1.18 1.142-1.18.723 0 1.141.533 1.141 1.18zm-.228 0c0-.533-.38-.951-.913-.951s-.913.38-.913.95c0 .533.38.952.913.952.57 0 .913-.419.913-.951zm-1.37-.533h.495c.266 0 .456.152.456.38 0 .153-.076.229-.19.305l.19.266v.038h-.266l-.19-.266h-.229v.266h-.266zm.495.228h-.229v.267h.229c.114 0 .152-.038.152-.114.038-.077-.038-.153-.152-.153zM7.602 12.4c.038-.151.076-.304.076-.456 0-.114-.038-.228-.038-.342-.114-.343-.304-.647-.646-.838l-4.87-2.777c-.685-.38-1.56-.152-1.94.533-.381.685-.153 1.56.532 1.94l2.701 1.56-2.701 1.56c-.685.38-.913 1.256-.533 1.94.38.685 1.256.914 1.94.533l4.832-2.777c.343-.267.571-.533.647-.876zm1.332 2.626c-.266-.038-.57.038-.837.19l-4.832 2.777c-.685.38-.913 1.256-.532 1.94.38.686 1.255.914 1.94.533l2.701-1.56v3.12c0 .8.647 1.408 1.446 1.408.799 0 1.407-.647 1.407-1.408v-5.592c0-.761-.57-1.37-1.293-1.408zm4.946-6.088c.266.038.57-.038.837-.19l4.832-2.777c.685-.38.913-1.256.532-1.94-.38-.686-1.255-.914-1.94-.533l-2.701 1.56V1.975c0-.799-.647-1.408-1.446-1.408-.799 0-1.446.609-1.446 1.408V7.53c0 .76.609 1.37 1.332 1.407zM3.265 5.97l4.832 2.777c.266.152.533.19.837.19.723-.038 1.331-.684 1.331-1.407V1.975c0-.799-.646-1.408-1.407-1.408-.799 0-1.446.647-1.446 1.408v3.12l-2.701-1.56c-.685-.38-1.56-.152-1.94.533-.419.646-.19 1.521.494 1.902zm9.093 6.011a.412.412 0 0 0-.114-.266l-.57-.571a.346.346 0 0 0-.267-.114.412.412 0 0 0-.266.114l-.571.57a.411.411 0 0 0-.114.267c0 .076.038.19.114.267l.57.57a.345.345 0 0 0 .267.114c.076 0 .19-.038.266-.114l.571-.57a.412.412 0 0 0 .114-.267zm1.598.533L11.94 14.53c-.039.038-.153.114-.229.114h-.608a.411.411 0 0 1-.267-.114L8.82 12.514a.408.408 0 0 1-.076-.229v-.608c0-.076.038-.19.114-.267l2.016-2.016a.41.41 0 0 1 .267-.114h.608a.41.41 0 0 1 .267.114l2.016 2.016a.347.347 0 0 1 .114.267v.608c-.076.077-.114.19-.19.229zm5.593 5.44l-4.832-2.777c-.266-.152-.57-.19-.837-.152-.723.038-1.332.684-1.332 1.408v5.554c0 .8.647 1.408 1.408 1.408.799 0 1.446-.647 1.446-1.408v-3.12l2.7 1.56c.686.38 1.561.152 1.941-.533.419-.646.19-1.521-.494-1.94zm2.549-7.533l-2.701 1.56 2.7 1.56c.686.38.914 1.256.533 1.94-.38.685-1.255.913-1.94.533l-4.832-2.778a1.644 1.644 0 0 1-.647-.798c-.037-.153-.076-.305-.076-.457 0-.114.039-.228.039-.342.114-.343.342-.647.646-.837l4.832-2.778c.685-.38 1.56-.152 1.94.533.457.609.19 1.484-.494 1.864"/>',
    "git":            '<path fill="currentColor" d="M13.09 23.549a1.54 1.54 0 0 1-2.18 0L.451 13.089a1.54 1.54 0 0 1 0-2.179l7.191-7.19 2.733 2.733a1.85 1.85 0 0 0 .964 2.326v6.66a1.849 1.849 0 1 0 1.54 0V8.957l2.508 2.508a1.85 1.85 0 1 0 1.09-1.09l-2.634-2.634a1.85 1.85 0 0 0-2.378-2.377L8.73 2.63 10.91.451a1.54 1.54 0 0 1 2.179 0l10.459 10.46a1.54 1.54 0 0 1 0 2.179z"/>',
    "github":         '<path fill="currentColor" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>',
    "apachespark":    '<path fill="currentColor" d="M10.812 0c-.425.013-.845.215-1.196.605a3.593 3.593 0 0 0-.493.722c-.355.667-.425 1.415-.556 2.143a551.9 551.9 0 0 0-.726 4.087c-.027.16-.096.227-.244.273C5.83 8.386 4.06 8.94 2.3 9.514c-.387.125-.773.289-1.114.506-1.042.665-1.196 1.753-.415 2.71.346.422.79.715 1.284.936 1.1.49 2.202.976 3.3 1.47.019.01.036.013.053.019h-.004l1.306.535c0 .023.002.045 0 .073-.2 2.03-.39 4.063-.58 6.095-.04.419-.012.831.134 1.23.317.87 1.065 1.148 1.881.701.372-.204.666-.497.937-.818 1.372-1.623 2.746-3.244 4.113-4.872.111-.133.205-.15.363-.098.349.117.697.231 1.045.347h.001c.02.012.045.02.073.03l.142.042c1.248.416 2.68.775 3.929 1.19.4.132.622.164 1.045.098.311-.048.592-.062.828-.236.602-.33.995-.957.988-1.682-.005-.427-.154-.813-.35-1.186-.82-1.556-1.637-3.113-2.461-4.666-.078-.148-.076-.243.037-.375 1.381-1.615 2.756-3.236 4.133-4.855.272-.32.513-.658.653-1.058.308-.878-.09-1.57-1-1.741a2.783 2.783 0 0 0-1.235.069c-1.974.521-3.947 1.041-5.918 1.57-.175.047-.26.015-.355-.144a353.08 353.08 0 0 0-2.421-4.018 4.61 4.61 0 0 0-.652-.849c-.371-.37-.802-.549-1.227-.536zm.172 3.703a.592.592 0 0 1 .189.211c.87 1.446 1.742 2.89 2.609 4.338.07.118.135.16.277.121 1.525-.41 3.052-.813 4.579-1.217.367-.098.735-.193 1.103-.289a.399.399 0 0 1-.1.2c-1.259 1.48-2.516 2.962-3.779 4.438-.11.13-.12.22-.04.37.937 1.803 1.768 3.309 2.498 4.76l-3.696-1.019c-.538-.18-1.077-.358-1.615-.539-.163-.055-.25-.03-.36.1-1.248 1.488-2.504 2.97-3.759 4.454a.398.398 0 0 1-.18.132c.035-.378.068-.757.104-1.136.149-1.572.297-3.144.451-4.716-.03-.318.117-.405-.322-.545-1.493-.593-3.346-1.321-4.816-1.905a.595.595 0 0 1 .24-.134c1.797-.57 3.595-1.14 5.394-1.705.127-.04.199-.092.211-.233.013-.148.05-.294.076-.441.241-1.363.483-2.726.726-4.088.068-.386.14-.771.21-1.157z"/>',
    "tensorflow":     '<path fill="currentColor" d="M1.292 5.856L11.54 0v24l-4.095-2.378V7.603l-6.168 3.564.015-5.31zm21.43 5.311l-.014-5.31L12.46 0v24l4.095-2.378V14.87l3.092 1.788-.018-4.618-3.074-1.756V7.603l6.168 3.564z"/>',
    "pytorch":        '<path fill="currentColor" d="M12.005 0L4.952 7.053a9.865 9.865 0 0 0 0 14.022 9.866 9.866 0 0 0 14.022 0c3.984-3.9 3.986-10.205.085-14.023l-1.744 1.743c2.904 2.905 2.904 7.634 0 10.538s-7.634 2.904-10.538 0-2.904-7.634 0-10.538l4.647-4.646.582-.665zm3.568 3.899a1.327 1.327 0 0 0-1.327 1.327 1.327 1.327 0 0 0 1.327 1.328A1.327 1.327 0 0 0 16.9 5.226 1.327 1.327 0 0 0 15.573 3.9z"/>',
}

SUBTOPIC_CATEGORIES: dict[str, dict[str, set[str]]] = {
    "aml": {
        "regulation": {"regulation", "regulatory", "regulate", "compliance", "law", "legal",
                       "proposal", "guidance", "directive", "policy", "rulling"},
        "crypto": {"crypto", "cryptocurrency", "bitcoin", "ethereum", "blockchain",
                   "digital asset", "token", "defi", "exchange"},
        "fraud": {"fraud", "scam", "money laundering", "sanctions", "illicit",
                  "suspicious", "ransomware", "phishing", "cybercrime"},
        "banking": {"bank", "banking", "fintech", "payment", "lending",
                    "financial", "credit", "capital", "institution"},
    },
    "stock": {
        "semiconductor": {"semiconductor", "chip", "foundry", "fab", "nvidia", "tsmc",
                          "asml", "intel", "amd", "processor", "gpu"},
        "ai": {"ai", "artificial intelligence", "machine learning", "deep learning",
               "neural", "llm", "openai", "anthropic", "google"},
        "stock_market": {"stock", "market", "nasdaq", "s&p", "valuation", "earnings",
                         "ipo", "trading", "investment"},
        "manufacturing": {"supply chain", "manufacturing", "production", "factory",
                          "industry", "industrial", "logistics"},
    },
    "data-engineering": {
        "pipeline": {"pipeline", "etl", "elt", "orchestration", "dag", "workflow",
                     "airflow", "dagster", "prefect", "kestra"},
        "storage": {"lake", "warehouse", "iceberg", "delta", "hudi", "parquet",
                    "arrow", "storage", "catalog", "schema"},
        "quality": {"quality", "test", "expectation", "monitoring", "observability",
                    "lineage", "contract", "soda", "great expectations"},
        "streaming": {"stream", "kafka", "flink", "beam", "event", "real-time",
                      "kafka connect", "debezium", "cdc"},
        "infrastructure": {"terraform", "kubernetes", "docker", "ci/cd", "cloud",
                           "deployment", "infrastructure", "platform"},
    },
}

PILLAR_COLORS = {
    "aml":              {"bg": BRAND["aml"]["darker"],     "fg": BRAND["aml"]["dark"],     "text": "#f8fafc", "accent": BRAND["aml"]["secondary"]},
    "stock":            {"bg": BRAND["markets"]["darker"], "fg": BRAND["markets"]["dark"],  "text": "#f0fdf4", "accent": BRAND["markets"]["secondary"]},
    "data-engineering": {"bg": BRAND["science"]["darker"], "fg": BRAND["science"]["dark"],  "text": "#eef2ff", "accent": BRAND["science"]["secondary"]},
}


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


# Brand icon keyword mappings — checked first so specific tech names
# map directly to brand SVGs (Simple Icons) before falling back to
# the general subtopic category matching.
BRAND_ICON_KEYWORDS: dict[str, set[str]] = {
    # Data engineering
    "kafka":       {"kafka", "confluent", "debezium", "avro", "ksqldb", "schema registry"},
    "kubernetes":  {"kubernetes", "k8s", "kube", "helm", "istio", "kubectl", "service mesh"},
    "terraform":   {"terraform", "iac", "infrastructure as code", "hcl", "opentofu"},
    "docker":      {"docker", "dockerfile", "docker compose"},
    "python":      {"python", "pandas", "numpy", "pyspark"},
    "postgresql":  {"postgresql", "postgres", "psql"},
    "snowflake":   {"snowflake", "snowpipe", "snowsql"},
    "git":         {"git", "version control"},
    "github":      {"github", "github actions"},
    "apachespark": {"spark", "apache spark", "pyspark", "databricks", "spark sql"},
    # ML / AI
    "tensorflow":  {"tensorflow", "keras"},
    "pytorch":     {"pytorch", "torch", "jax"},
}


def _pick_subtopic(titles: list[str], pillar: str) -> str:
    """Pick the most relevant subtopic/icon based on article titles.

    Checks brand icon keywords first so specific tech names (Kafka, Kubernetes, etc.)
    map directly to brand SVGs. Falls back to general subtopic category matching.
    """
    text = " ".join(titles).lower()

    # 1) Check brand icon keywords first (word-boundary matching to avoid false positives)
    for icon, keywords in BRAND_ICON_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf'(?<![a-z]){re.escape(kw)}(?![a-z])', text):
                return icon

    # 2) Fall back to general subtopic category matching
    subs = SUBTOPIC_CATEGORIES.get(pillar, {})
    best_sub = list(subs.keys())[0] if subs else "regulation"
    best_score = 0
    for sub, keywords in subs.items():
        score = sum(2 if kw in text else 0 for kw in keywords)
        if score > best_score:
            best_score = score
            best_sub = sub
    return best_sub


def _extract_topic_words(titles: list[str], n: int = 5) -> list[str]:
    """Extract the most meaningful topic words from titles."""
    text = " ".join(titles)
    words = re.findall(r"[A-Z][a-z]{3,}", text)
    stop = {"This", "That", "With", "From", "What", "How", "Why", "When",
            "After", "Before", "Into", "Over", "Also", "Just", "More",
            "Very", "New", "First", "Last", "Next", "They", "Them", "Their"}
    words = [w for w in words if w not in stop]
    from collections import Counter
    counts = Counter(words)
    return [w for w, _ in counts.most_common(n)]


# ────────────── Fractal Engine ──────────────

def _hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    t = max(0.0, min(1.0, t))
    return _rgb_to_hex(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return _rgb_to_hex(int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _det_rand(seed: int, i: int = 0) -> float:
    """Deterministic pseudo-random from seed + index."""
    h = hashlib.md5(f"{seed}:{i}".encode()).hexdigest()
    return int(h[:8], 16) / 0xffffffff


def _det_rand_range(seed: int, i: int, lo: float, hi: float) -> float:
    return lo + _det_rand(seed, i) * (hi - lo)


def _det_rand_int(seed: int, i: int, lo: int, hi: int) -> int:
    return int(_det_rand(seed, i) * (hi - lo + 1)) + lo


# ───── Fractal Type: L-System Tree ─────

def _fractal_tree(elems: list, seed: int, pal: dict, w: int, h: int,
                  cx: float, cy: float, trunk: float, depth: int,
                  mirror_x: bool, mirror_y: bool, seq: list):
    """Recursive L-system branching tree with rounded caps and color transitions."""
    angle = -90 + _det_rand_range(seed, seq[0], -15, 15)
    seq[0] += 1
    spread = 20 + _det_rand_range(seed, seq[0], 10, 40)
    seq[0] += 1
    ratio = 0.62 + _det_rand_range(seed, seq[0], 0, 0.18)
    seq[0] += 1
    lean = _det_rand_range(seed, seq[0], -10, 10)
    seq[0] += 1

    def _branch(x, y, a, length, d):
        if d <= 0 or length < 3:
            return
        rad = math.radians(a)
        ex = x + length * math.cos(rad)
        ey = y + length * math.sin(rad)
        t = 1.0 - d / depth
        sw = max(0.5, 3.0 * t)
        op = 0.15 + 0.5 * t
        color = _lerp_color(pal["fg"], pal["accent"], t * 0.7)
        elems.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{color}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        if d <= 2 and t > 0.3:
            glow_r = 2 + t * 8
            elems.append(
                f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{glow_r:.0f}" '
                f'fill="{pal["accent"]}" opacity="{op * 0.15:.2f}"/>'
            )
        n = 1 + _det_rand_int(seed, d * 10 + int(x + y), 2, 3)
        for i in range(n):
            off = (i - (n - 1) / 2) * spread / (n - 1) if n > 1 else 0
            child_a = a + off + lean * (1 - t)
            child_l = length * (ratio + _det_rand_range(seed, d * 100 + i * 10, -0.05, 0.05))
            _branch(ex, ey, child_a, child_l, d - 1)

    _branch(cx, cy, angle, trunk, depth)


# ───── Fractal Type: Sierpinski Triangle ─────

def _fractal_sierpinski(elems: list, seed: int, pal: dict, w: int, h: int,
                        x1: float, y1: float, x2: float, y2: float,
                        x3: float, y3: float, depth: int, seq: list):
    """Recursive Sierpinski triangle with color fills and rounded lines."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t)
        op = 0.08 + t * 0.15
        elems.append(
            f'<polygon points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} {x3:.1f},{y3:.1f}" '
            f'fill="{c}" opacity="{op:.2f}" stroke="{pal["accent"]}" '
            f'stroke-width="0.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        return
    mx1 = (x1 + x2) / 2
    my1 = (y1 + y2) / 2
    mx2 = (x2 + x3) / 2
    my2 = (y2 + y3) / 2
    mx3 = (x3 + x1) / 2
    my3 = (y3 + y1) / 2
    _fractal_sierpinski(elems, seed, pal, w, h, x1, y1, mx1, my1, mx3, my3, depth - 1, seq)
    _fractal_sierpinski(elems, seed, pal, w, h, mx1, my1, x2, y2, mx2, my2, depth - 1, seq)
    _fractal_sierpinski(elems, seed, pal, w, h, mx3, my3, mx2, my2, x3, y3, depth - 1, seq)


# ───── Fractal Type: Koch Snowflake ─────

def _fractal_koch(elems: list, seed: int, pal: dict, w: int, h: int,
                  x1: float, y1: float, x2: float, y2: float,
                  depth: int, seq: list, hue_offset: float = 0):
    """Recursive Koch curve with dynamic hue-shifted coloring."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t * 0.8)
        sw = 0.8 + t * 1.5
        op = 0.2 + t * 0.4
        elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        return
    dx = (x2 - x1) / 3
    dy = (y2 - y1) / 3
    p1x = x1 + dx
    p1y = y1 + dy
    p2x = x1 + dx * 2
    p2y = y1 + dy * 2
    angle = math.radians(60)
    p3x = p1x + (dx * math.cos(angle) - dy * math.sin(angle))
    p3y = p1y + (dx * math.sin(angle) + dy * math.cos(angle))
    _fractal_koch(elems, seed, pal, w, h, x1, y1, p1x, p1y, depth - 1, seq, hue_offset)
    _fractal_koch(elems, seed, pal, w, h, p1x, p1y, p3x, p3y, depth - 1, seq, hue_offset + 20)
    _fractal_koch(elems, seed, pal, w, h, p3x, p3y, p2x, p2y, depth - 1, seq, hue_offset - 20)
    _fractal_koch(elems, seed, pal, w, h, p2x, p2y, x2, y2, depth - 1, seq, hue_offset)


# ───── Fractal Type: Dragon Curve ─────

def _fractal_dragon(elems: list, seed: int, pal: dict, w: int, h: int,
                    x1: float, y1: float, x2: float, y2: float,
                    depth: int, seq: list, sign: float = 1):
    """Recursive dragon curve with rounded segments and color shift."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        c = _lerp_color(pal["fg"], pal["accent"], t)
        sw = 0.5 + t * 2.0
        op = 0.1 + t * 0.4
        elems.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{c}" stroke-width="{sw:.1f}" opacity="{op:.2f}" '
            f'stroke-linecap="round"/>'
        )
        return
    mx = (x1 + x2) / 2 + (y2 - y1) / 2 * sign
    my = (y1 + y2) / 2 - (x2 - x1) / 2 * sign
    _fractal_dragon(elems, seed, pal, w, h, x1, y1, mx, my, depth - 1, seq, 1)
    _fractal_dragon(elems, seed, pal, w, h, x2, y2, mx, my, depth - 1, seq, -1)


# ───── Fractal Type: Barnsley Fern (IFS) ─────

def _fractal_fern(elems: list, seed: int, pal: dict, w: int, h: int,
                  seq: list, count: int = 300):
    """Barnsley fern IFS rendered as rounded dots with color gradient."""
    x, y = 0.0, 0.0
    for i in range(count):
        r = _det_rand(seed, seq[0] + i)
        seq[0] += 1
        if r < 0.01:
            nx, ny = 0.0, 0.16 * y
        elif r < 0.86:
            nx, ny = 0.85 * x + 0.04 * y, -0.04 * x + 0.85 * y + 1.6
        elif r < 0.93:
            nx, ny = 0.2 * x - 0.26 * y, 0.23 * x + 0.22 * y + 1.6
        else:
            nx, ny = -0.15 * x + 0.28 * y, 0.26 * x + 0.24 * y + 0.44
        x, y = nx, ny
        px = w / 2 + x * (w / 12)
        py = h * 0.92 - y * (h / 12)
        t = i / count
        c = _lerp_color(pal["accent"], pal["fg"], t)
        op = 0.15 + t * 0.3
        r_size = 0.8 + t * 1.5
        elems.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_size:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )


# ───── Fractal Type: Spiraling Circles ─────

def _fractal_spiral(elems: list, seed: int, pal: dict, w: int, h: int,
                    cx: float, cy: float, seq: list, turns: int = 8):
    """Golden-ratio spiral of nested circles with color transitions."""
    angle_step = 137.5  # golden angle
    shrink = 0.92 + _det_rand_range(seed, seq[0], 0, 0.06)
    seq[0] += 1
    r = min(w, h) * 0.08
    for i in range(turns * 8):
        angle = math.radians(i * angle_step)
        nx = cx + i * 2.5 * math.cos(angle)
        ny = cy + i * 2.5 * math.sin(angle)
        if nx < 0 or nx > w or ny < 0 or ny > h:
            continue
        radius = max(1.0, r * (shrink ** i))
        t = i / (turns * 8)
        c = _lerp_color(pal["accent"], pal["fg"], t)
        op = 0.05 + t * 0.2
        elems.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{radius:.1f}" '
            f'fill="none" stroke="{c}" stroke-width="0.8" opacity="{op:.2f}"/>'
        )
        if i % 3 == 0:
            inner_r = radius * 0.4
            inner_c = _lerp_color(pal["fg"], pal["accent"], 1 - t)
            elems.append(
                f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{inner_r:.1f}" '
                f'fill="{inner_c}" opacity="{op * 0.5:.2f}"/>'
            )


# ───── Fractal Type: Hilbert Curve ─────

def _fractal_hilbert(elems: list, seed: int, pal: dict, w: int, h: int,
                     x: float, y: float, xi: float, xj: float,
                     yi: float, yj: float, depth: int, seq: list):
    """Recursive Hilbert space-filling curve with color gradient."""
    if depth <= 0:
        t = _det_rand(seed, seq[0])
        seq[0] += 1
        nx = x + (xi + yi) / 2
        ny = y + (xj + yj) / 2
        c = _lerp_color(pal["fg"], pal["accent"], t)
        sw = 0.5 + t * 2.0
        op = 0.15 + t * 0.35
        elems.append(
            f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="{sw:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )
        return
    _fractal_hilbert(elems, seed, pal, w, h, x, y, yi / 2, yj / 2, xi / 2, xj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2, y + xj / 2, xi / 2, xj / 2, yi / 2, yj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2 + yi / 2, y + xj / 2 + yj / 2, xi / 2, xj / 2, yi / 2, yj / 2, depth - 1, seq)
    _fractal_hilbert(elems, seed, pal, w, h, x + xi / 2 + yi, y + xj / 2 + yj, -yi / 2, -yj / 2, -xi / 2, -xj / 2, depth - 1, seq)


# ───── Mirror helper ─────

def _mirror_elements(elems: list, mirror_x: bool, mirror_y: bool,
                     w: int, h: int) -> list:
    """Duplicate elements with mirror transformations."""
    if not mirror_x and not mirror_y:
        return elems
    out = list(elems)
    for el in elems:
        m = el
        if mirror_x:
            m = m.replace(f'x1="', f'x1="{-1 if "x1" in m else ""}')
            # Simple approach: wrap in <use> with transform
        if mirror_y:
            m = m.replace(f'y1="', f'y1="')
    return out


def _generate_mist(seed: int, pal: dict, w: int, h: int, count: int,
                   seq: list) -> list:
    """Generate atmospheric mist particles."""
    elems = []
    for i in range(count):
        x = _det_rand_range(seed, seq[0] + i, 0, w)
        y = _det_rand_range(seed, seq[0] + i + 100, 0, h)
        r = _det_rand_range(seed, seq[0] + i + 200, 1, 6)
        op = _det_rand_range(seed, seq[0] + i + 300, 0.01, 0.08)
        c = _lerp_color(pal["accent"], pal["text"], _det_rand(seed, seq[0] + i + 400))
        elems.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
            f'fill="{c}" opacity="{op:.2f}"/>'
        )
    seq[0] += count + 500
    return elems


def _overlay_panel_svg(featured_image_url: str, fallback_icons: list | None,
                        layer: str, pal: dict, width: int, height: int) -> tuple[list[str], list[str]]:
    """Generate SVG elements for the image/fallback overlay panel.

    Returns (defs, elements) where defs go inside <defs> and elements are rendered in order.

    Research: image left (4/7 width), Learn: image right (4/7 width),
    Knowledge: image top (4/7 height). Includes rounded background,
    accent border, and a shadow gradient at the panel edge for seamless
    transition between image and fractal background.
    """
    defs = []
    elems = []
    if layer == "research":
        ix, iy, iw, ih = 0, 0, int(width * 4 / 7), height
    elif layer == "learn":
        ix, iy, iw, ih = int(width * 3 / 7), 0, int(width * 4 / 7), height
    elif layer == "knowledge":
        ix, iy, iw, ih = 0, 0, width, int(height * 4 / 7)
    else:
        return defs, elems

    r = 4

    if featured_image_url:
        # Background fallback (shows if image fails to load)
        elems.append(
            f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}"'
            f' fill="{pal["bg"]}" rx="{r}" opacity="0.3"/>'
        )
        # Clip path for rounded image corners
        clip_id = f"clip-{layer}-{ix}-{iy}"
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'  <rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="{r}"/>'
            f'</clipPath>'
        )
        elems.append(
            f'<image href="{featured_image_url}" x="{ix}" y="{iy}"'
            f' width="{iw}" height="{ih}"'
            f' preserveAspectRatio="xMidYMid slice"'
            f' clip-path="url(#{clip_id})"/>'
        )
        # Accent border
        elems.append(
            f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}"'
            f' rx="{r}" fill="none" stroke="{pal["accent"]}"'
            f' stroke-width="1.5" opacity="0.35"/>'
        )
        # Shadow gradient at panel edge — fade image into fractal
        if layer == "research":
            sid = f"shadow-{layer}"
            defs.append(
                f'<linearGradient id="{sid}" x1="0" y1="0" x2="1" y2="0">'
                f'<stop offset="0" stop-color="{pal["bg"]}" stop-opacity="0"/>'
                f'<stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0.7"/>'
                f'</linearGradient>'
            )
            elems.append(
                f'<rect x="{ix + iw - 24}" y="{iy}" width="24" height="{ih}"'
                f' fill="url(#{sid})"/>'
            )
        elif layer == "learn":
            sid = f"shadow-{layer}"
            defs.append(
                f'<linearGradient id="{sid}" x1="1" y1="0" x2="0" y2="0">'
                f'<stop offset="0" stop-color="{pal["bg"]}" stop-opacity="0"/>'
                f'<stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0.7"/>'
                f'</linearGradient>'
            )
            elems.append(
                f'<rect x="{ix}" y="{iy}" width="24" height="{ih}"'
                f' fill="url(#{sid})"/>'
            )
        elif layer == "knowledge":
            sid = f"shadow-{layer}"
            defs.append(
                f'<linearGradient id="{sid}" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{pal["bg"]}" stop-opacity="0"/>'
                f'<stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0.7"/>'
                f'</linearGradient>'
            )
            elems.append(
                f'<rect x="{ix}" y="{iy + ih - 24}" width="{iw}" height="24"'
                f' fill="url(#{sid})"/>'
            )
    elif fallback_icons:
        elems.append(
            f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}"'
            f' fill="{pal["bg"]}" opacity="0.85" rx="{r}"/>'
        )
        n = min(3, len(fallback_icons))
        for idx, path_data in enumerate(fallback_icons[:3]):
            cx_pos = ix + (iw / (n + 1)) * (idx + 1)
            cy_pos = iy + ih / 2
            elems.append(
                f'<g transform="translate({cx_pos:.0f}, {cy_pos:.0f}) scale(0.6)"'
                f' color="{pal["accent"]}" opacity="0.8">'
                f'  {path_data}'
                f'</g>'
            )
    return defs, elems


def generate_thumbnail_svg(title: str, pillar: str, scores: dict,
                           width: int = 600, height: int = 340,
                           featured_image_url: str = "",
                           layer: str = "research",
                           fallback_icons: list | None = None) -> str:
    """Generate a unique fractal-based SVG thumbnail for a blog post.

    Uses 7 fractal types, mirroring, dynamic color transitions, and
    atmospheric effects — each image is uniquely derived from the title hash.
    When featured_image_url is provided, overlays a 4/7 image panel per layer.
    Falls back to 3 tag-derived topic icons when no image is available.
    """
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])
    words = _extract_topic_words([title], 3)
    h = _content_hash(title)
    seed = int(h[:12], 16)
    seq = [0]

    # Fractal type (0-6)
    ftype = _det_rand_int(seed, seq[0], 0, 6)
    seq[0] += 1

    # Mirror modes: 0=none, 1=h, 2=v, 3=both
    mirror_mode = _det_rand_int(seed, seq[0], 0, 3)
    seq[0] += 1
    mirror_x = mirror_mode in (1, 3)
    mirror_y = mirror_mode in (2, 3)

    # Background gradient variant
    bg_v = _det_rand_int(seed, seq[0], 0, 3)
    seq[0] += 1
    color_tint = _lerp_color(pal["bg"], pal["accent"], 0.08 + _det_rand(seed, seq[0]) * 0.1)
    seq[0] += 1

    if bg_v == 0:
        bg = (f'<linearGradient id="bg-{h[:8]}" x1="0" y1="0" x2="1" y2="1">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset="0.5" stop-color="{color_tint}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')
    elif bg_v == 1:
        bg = (f'<radialGradient id="bg-{h[:8]}" cx="{30 + _det_rand_int(seed, seq[0], 0, 40)}%" '
              f'cy="{30 + _det_rand_int(seed, seq[0] + 1, 0, 40)}%">'
              f'<stop offset="0" stop-color="{color_tint}"/>'
              f'<stop offset="1" stop-color="{pal["bg"]}"/>'
              f'</radialGradient>')
        seq[0] += 2
    else:
        c2 = _lerp_color(pal["bg"], pal["accent"], 0.18)
        bg = (f'<linearGradient id="bg-{h[:8]}" x1="0" y1="1" x2="1" y2="0">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset="0.4" stop-color="{color_tint}"/>'
              f'<stop offset="0.7" stop-color="{c2}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')

    # Radial accent glow
    glow_cx = _det_rand_int(seed, seq[0], 20, 80)
    glow_cy = _det_rand_int(seed, seq[0] + 1, 20, 80)
    seq[0] += 2
    glow_op = 0.08 + _det_rand(seed, seq[0]) * 0.12
    seq[0] += 1

    # Overlay panel defs/elems (must be before lines list since defs go in <defs>)
    overlay_defs, overlay_elems = _overlay_panel_svg(
        featured_image_url, fallback_icons, layer, pal, width, height
    )

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}">',
        '<defs>',
        bg,
        *overlay_defs,
        (f'<radialGradient id="glow-{h[:8]}" cx="{glow_cx}%" cy="{glow_cy}%">'
         f'<stop offset="0" stop-color="{pal["accent"]}" stop-opacity="{glow_op:.2f}"/>'
         f'<stop offset="1" stop-color="{pal["bg"]}" stop-opacity="0"/>'
         f'</radialGradient>'),
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="url(#bg-{h[:8]})"/>',
        f'<rect width="{width}" height="{height}" fill="url(#glow-{h[:8]})"/>',
    ]

    # Mist layer 1 (background)
    mist1 = _generate_mist(seed, pal, width, height,
                           8 + _det_rand_int(seed, seq[0], 0, 4), seq)
    seq[0] += 1
    lines.extend(mist1)

    # Fractal elements
    fractal_elems = []
    cx, cy = width // 2, height // 2

    if ftype == 0:
        # L-System Tree — grows from bottom-center with optional mirror branches
        tree_x = width / 2 + (_det_rand_range(seed, seq[0], -40, 40))
        tree_y = height * 0.92
        trunk = 60 + _det_rand_range(seed, seq[0] + 1, 30, 80)
        depth = _det_rand_int(seed, seq[0] + 2, 3, 5)
        seq[0] += 3
        _fractal_tree(fractal_elems, seed, pal, width, height,
                       tree_x, tree_y, trunk, depth, mirror_x, mirror_y, seq)
        if mirror_x:
            _fractal_tree(fractal_elems, seed + 999, pal, width, height,
                           width - tree_x, tree_y, trunk, depth, False, False, seq)

    elif ftype == 1:
        # Sierpinski Triangle
        size = min(width, height) * 0.7
        depth = _det_rand_int(seed, seq[0], 3, 5)
        seq[0] += 1
        ox = (width - size) / 2
        oy = (height - size) / 2
        _fractal_sierpinski(fractal_elems, seed, pal, width, height,
                            ox + size / 2, oy,
                            ox, oy + size,
                            ox + size, oy + size,
                            depth, seq)
        if mirror_x:
            _fractal_sierpinski(fractal_elems, seed + 999, pal, width, height,
                                width - (ox + size / 2), oy,
                                width - ox, oy + size,
                                width - (ox + size), oy + size,
                                depth, seq)

    elif ftype == 2:
        # Koch Snowflake (3 sides)
        size = min(width, height) * 0.55
        depth = _det_rand_int(seed, seq[0], 2, 4)
        seq[0] += 1
        cx_k = width / 2
        cy_k = height / 2 - size * 0.2
        r_k = size
        for i in range(3):
            a1 = math.radians(60 + i * 120)
            a2 = math.radians(60 + (i + 1) * 120)
            x1 = cx_k + r_k * math.cos(a1)
            y1 = cy_k + r_k * math.sin(a1)
            x2 = cx_k + r_k * math.cos(a2)
            y2 = cy_k + r_k * math.sin(a2)
            _fractal_koch(fractal_elems, seed + i, pal, width, height,
                          x1, y1, x2, y2, depth, seq, i * 30)
        if mirror_x:
            seq[0] += 10
            _fractal_koch(fractal_elems, seed + 999, pal, width, height,
                          width - x1, y1, width - x2, y2, depth, seq, 0)

    elif ftype == 3:
        # Dragon Curve (depth capped at 6 to avoid 5000+ line SVGs)
        depth = _det_rand_int(seed, seq[0], 4, 6)
        seq[0] += 1
        start_x = width * _det_rand_range(seed, seq[0], 0.1, 0.4)
        start_y = height * _det_rand_range(seed, seq[0] + 1, 0.2, 0.8)
        end_x = width * _det_rand_range(seed, seq[0] + 2, 0.6, 0.9)
        end_y = height * _det_rand_range(seed, seq[0] + 3, 0.2, 0.8)
        seq[0] += 4
        _fractal_dragon(fractal_elems, seed, pal, width, height,
                        start_x, start_y, end_x, end_y, depth, seq)

    elif ftype == 4:
        # Barnsley Fern
        count = 60 + _det_rand_int(seed, seq[0], 0, 40)
        seq[0] += 1
        _fractal_fern(fractal_elems, seed, pal, width, height, seq, count)

    elif ftype == 5:
        # Spiraling Circles
        turns = _det_rand_int(seed, seq[0], 5, 10)
        seq[0] += 1
        _fractal_spiral(fractal_elems, seed, pal, width, height,
                        width / 2, height / 2, seq, turns)

    else:
        # Hilbert Curve (as point cloud — depth capped at 3 to avoid 1000+ circles)
        depth = _det_rand_int(seed, seq[0], 2, 3)
        seq[0] += 1
        size = min(width, height) * 0.5
        ox = (width - size) / 2
        oy = (height - size) / 2
        _fractal_hilbert(fractal_elems, seed, pal, width, height,
                         ox, oy, size, 0, 0, size, depth, seq)

    lines.extend(fractal_elems)

    # Mist layer 2 (foreground, over fractal)
    mist2 = _generate_mist(seed + 1000, pal, width, height,
                           4 + _det_rand_int(seed, seq[0], 0, 4), seq)
    seq[0] += 1
    lines.extend(mist2)

    lines.extend(overlay_elems)

    # Topic icon — positioned on the visible fractal area (opposite side of image panel)
    panel_w = int(width * 4 / 7)
    if layer == "learn":
        # Image on right → icon on left side of fractal area
        icon_x = 14 + _det_rand_int(seed, seq[0], 0, 20)
    elif layer == "knowledge":
        # Image on top → icon centered in bottom fractal strip
        icon_x = width // 2 - 20 + _det_rand_int(seed, seq[0], -20, 20)
    else:
        # Research/default: image on left → icon on right side
        icon_x = panel_w + 14 + _det_rand_int(seed, seq[0], 0, 20)
    icon_y = height - 56 + _det_rand_int(seed, seq[0] + 1, 0, 10)
    icon_scale = 0.6 + _det_rand(seed, seq[0] + 2) * 0.3
    seq[0] += 3
    lines.extend([
        f'<g transform="translate({icon_x:.0f}, {icon_y:.0f}) scale({icon_scale:.2f})"'
        f' color="{pal["accent"]}" opacity="0.8">',
        f'  {icon_path}',
        f'</g>',
    ])

    # Topic words as floating tags (bottom-right)
    for i, w in enumerate(words[:2]):
        tx = width - 80 + _det_rand_int(seed, seq[0] + i, -30, 30)
        ty = height - 30 + i * 18
        op = 0.15 + _det_rand(seed, seq[0] + i + 10) * 0.15
        lines.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" fill="{pal["accent"]}"'
            f' font-family="system-ui,sans-serif" font-size="11" font-weight="600"'
            f' opacity="{op:.2f}">{w}</text>'
        )
    seq[0] += 20

    # SQI indicator bar (subtle, bottom-center; only when signal data exists)
    bar_y = height - 10
    if "sqi" in scores:
        sqi = scores["sqi"]
        bar_w = max(2, int(sqi * (width * 0.3)))
        lines.append(
            f'<rect x="{width / 2 - width * 0.15:.0f}" y="{bar_y}"'
            f' width="{width * 0.3:.0f}" height="2" rx="1" fill="{pal["text"]}" opacity="0.06"/>'
        )
        lines.append(
            f'<rect x="{width / 2 - width * 0.15:.0f}" y="{bar_y}"'
            f' width="{bar_w}" height="2" rx="1" fill="{pal["accent"]}" opacity="0.4"/>'
        )

    # Pillar label (subtle, bottom-center near SQI)
    lines.append(
        f'<text x="{width / 2 + width * 0.15 + 6:.0f}" y="{bar_y + 10}"'
        f' fill="{pal["accent"]}" font-family="system-ui,sans-serif"'
        f' font-size="8" font-weight="600" opacity="0.25">{pillar.upper()}</text>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


def generate_og_image(title: str, pillar: str, scores: dict,
                      date_str: str = "",
                      featured_image_url: str = "",
                      layer: str = "research",
                      fallback_icons: list | None = None) -> str:
    """Generate a social sharing OG image SVG with the article title and fractal backing.

    When featured_image_url is provided, overlays a 4/7 image panel per layer
    behind the title/meta content. Falls back to tag-derived topic icons.
    """
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    sub = _pick_subtopic([title], pillar)
    icon_path = TOPIC_ICONS.get(sub, TOPIC_ICONS["regulation"])
    h = _content_hash(title)
    seed = int(h[:12], 16)
    seq = [0]

    # Wrap title text
    words_t = title.split()
    lines_text = []
    line = ""
    for w in words_t:
        if len(line + w) > 40:
            lines_text.append(line.strip())
            line = w + " "
        else:
            line += w + " "
    lines_text.append(line.strip())
    title_lines = lines_text[:4]

    # Dynamic background with fractal elements
    bg_v = _det_rand_int(seed, seq[0], 0, 2)
    seq[0] += 1
    c_tint = _lerp_color(pal["bg"], pal["accent"], 0.12)

    if bg_v == 0:
        bg = (f'<linearGradient id="ogbg" x1="0" y1="0" x2="1" y2="1">'
              f'<stop offset="0" stop-color="{pal["bg"]}"/>'
              f'<stop offset=".5" stop-color="{c_tint}"/>'
              f'<stop offset="1" stop-color="{pal["fg"]}"/>'
              f'</linearGradient>')
    else:
        bg = (f'<radialGradient id="ogbg" cx="{40 + _det_rand_int(seed, seq[0], 0, 30)}%"'
              f' cy="{40 + _det_rand_int(seed, seq[0] + 1, 0, 30)}%">'
              f'<stop offset="0" stop-color="{c_tint}"/>'
              f'<stop offset="1" stop-color="{pal["bg"]}"/>'
              f'</radialGradient>')
        seq[0] += 2

    # Decorative fractal circles
    circles = []
    for i in range(6):
        r_x = 80 + _det_rand_int(seed, seq[0] + i * 3, 0, 200)
        r_y = 80 + _det_rand_int(seed, seq[0] + i * 3 + 1, 0, 150)
        cx_c = _det_rand_int(seed, seq[0] + i * 3 + 2, 100, 1100)
        cy_c = _det_rand_int(seed, seq[0] + i * 3 + 3, 50, 550)
        op_c = 0.015 + _det_rand(seed, seq[0] + i * 3 + 4) * 0.03
        circles.append(
            f'<ellipse cx="{cx_c}" cy="{cy_c}" rx="{r_x}" ry="{r_y}"'
            f' fill="{pal["accent"]}" opacity="{op_c:.2f}"/>'
        )
    seq[0] += 20

    # Subtle fractal mist overlay
    mist = _generate_mist(seed, pal, 1200, 630, 12, seq)

    # Image/fallback overlay panel (before content, so text renders on top)
    overlay_defs, overlay_elems = _overlay_panel_svg(
        featured_image_url, fallback_icons, layer, pal, 1200, 630
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">',
        '<defs>', bg, *overlay_defs, '</defs>',
        f'<rect width="1200" height="630" fill="url(#ogbg)"/>',
    ] + circles + mist + overlay_elems + [
        f'<!-- Icon -->',
        f'<g transform="translate(50, 50) scale(1.8)"'
        f' color="{pal["accent"]}">',
        f'  {icon_path}',
        f'</g>',
    ]

    # Title lines
    y = 260
    for tl in title_lines:
        parts.append(
            f'<text x="50" y="{y}" fill="{pal["text"]}" font-family="system-ui,sans-serif"'
            f' font-size="{44 if len(tl) < 35 else 36}" font-weight="700">'
            f'{tl.replace("&", "&amp;").replace("<", "&lt;")}</text>'
        )
        y += 52

    # Meta info with accent glow bar (SQI bar only when signal data exists)
    parts.extend([
        f'<text x="50" y="500" fill="{pal["accent"]}" font-family="system-ui,sans-serif"'
        f' font-size="18" font-weight="600">AcaciaFund &nbsp;·&nbsp; {pillar.upper()}'
        f'{" &nbsp;·&nbsp; " + date_str if date_str else ""}</text>',
        f'<text x="50" y="540" fill="{pal["text"]}" font-family="system-ui,sans-serif"'
        f' font-size="14" opacity="0.5">Codzienna synteza badan — AML, rynki, nauka</text>',
    ])
    if "sqi" in scores:
        sqi = scores["sqi"]
        parts.append(
            f'<rect x="50" y="570" width="{int(min(1.0, sqi) * 200)}" height="4" rx="2"'
            f' fill="{pal["accent"]}" opacity="0.8"/>'
        )
    parts.append('</svg>')

    return "\n".join(parts)


def generate_topic_badge(name: str, pillar: str, count: int = 0) -> str:
    """Generate a small SVG badge for a topic/category."""
    pal = PILLAR_COLORS.get(pillar, PILLAR_COLORS["aml"])
    w = max(60, len(name) * 8 + 24)
    count_text = f" ({count})" if count else ""
    total_w = w + (len(count_text) * 8 if count_text else 0)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="28" viewBox="0 0 {total_w} 28">'
        f'  <rect width="{total_w}" height="28" rx="14" fill="{pal["fg"]}"/>'
        f'  <text x="14" y="18" fill="{pal["text"]}" font-family="system-ui,sans-serif" font-size="12" '
        f'font-weight="600">{name}{count_text}</text>'
        f'</svg>'
    )


def generate_signal_meter(sqi: float, width: int = 200) -> str:
    """Generate an SVG signal quality meter bar."""
    bar_w = int(min(1.0, max(0, sqi)) * width)
    color = "#22c55e" if sqi >= 0.6 else "#d97706" if sqi >= 0.35 else "#ef4444"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="16" viewBox="0 0 {width} 16">'
        f'  <rect width="{width}" height="6" y="5" rx="3" fill="var(--color-border, #e2e8f0)"/>'
        f'  <rect width="{bar_w}" height="6" y="5" rx="3" fill="{color}"/>'
        f'  <circle cx="{max(6, bar_w)}" cy="8" r="5" fill="{color}"/>'
        f'  <text x="{width + 8}" y="13" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="11">{sqi:.2f}</text>'
        f'</svg>'
    )


def generate_all_thumbnails(pillar_stories: dict[str, list[dict]],
                             pillar_signals: dict[str, dict]) -> dict[str, str]:
    """Generate thumbnails for all stories across all pillars."""
    results: dict[str, str] = {}
    for pillar, stories in pillar_stories.items():
        for story in stories:
            title = story.get("title", "")
            key = hashlib.md5(title.encode()).hexdigest()[:12]
            scores = {"sqi": 0.5}
            signals = pillar_signals.get(pillar, {})
            if signals:
                scores["sqi"] = signals.get("avg_sqi", 0.5)
            svg = generate_thumbnail_svg(title, pillar, scores)
            fname = f"thumb_{key}.svg"
            fpath = STATIC_DIR / fname
            fpath.write_text(svg, encoding="utf-8")
            results[title] = f"/images/{fname}"
    return results


def generate_post_thumbnail_block(title: str, pillar: str, scores: dict) -> str:
    """Generate a complete HTML block with inline SVG for embedding in post content."""
    svg = generate_thumbnail_svg(title, pillar, scores, width=800, height=400)
    return f'<div class="post-visual">{svg}</div>'


# ──────────────────────────────────────────────
# Phase 2: Zero-JS SVG Chart Engine
# ──────────────────────────────────────────────

SOURCE_COLORS = {"hn": "#f59e0b", "arxiv": "#3b82f6", "pubmed": "#22c55e"}
SOURCE_LABELS = {"hn": "HN", "arxiv": "arXiv", "pubmed": "PubMed"}
BLOOM_COLORS = {
    "remember": "#60a5fa", "understand": "#4ade80", "apply": "#fbbf24",
    "analyze": "#a78bfa", "evaluate": "#f87171", "create": "#818cf8",
}
BLOOM_LABELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]


def source_bar_svg(breakdown: dict, width: int = 280, height: int = 80) -> str:
    """Horizontal stacked bar showing HN / arXiv / PubMed source proportions."""
    total = sum(breakdown.get(k, 0) for k in ("hn", "arxiv", "pubmed")) or 1
    bar_x = 50
    bar_w = width - bar_x - 10
    bar_h = 20
    y = 10
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    x = bar_x
    for key in ("hn", "arxiv", "pubmed"):
        val = breakdown.get(key, 0)
        if val <= 0:
            continue
        seg_w = max(2, int(val / total * bar_w))
        c = SOURCE_COLORS.get(key, "#94a3b8")
        label = SOURCE_LABELS.get(key, key)
        parts.append(f'<rect x="{x}" y="{y}" width="{seg_w}" height="{bar_h}" rx="3" fill="{c}" opacity="0.9"/>')
        parts.append(f'<text x="{x + 6}" y="{y + 14}" fill="#fff" font-family="system-ui,sans-serif" font-size="10" font-weight="600">{label} {val}</text>')
        x += seg_w
    # Scale ticks
    for pct in (0, 25, 50, 75, 100):
        tx = bar_x + int(pct / 100 * bar_w)
        parts.append(f'<line x1="{tx}" y1="{y + bar_h + 2}" x2="{tx}" y2="{y + bar_h + 6}" stroke="var(--color-text-muted, #94a3b8)" stroke-width="0.5"/>')
        parts.append(f'<text x="{tx}" y="{y + bar_h + 16}" text-anchor="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="7">{pct}%</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def sparkline_svg(values: list[float], color: str = "#22c55e",
                  width: int = 160, height: int = 40) -> str:
    """Mini sparkline chart for trends (e.g. SQI across articles)."""
    if not values:
        values = [0]
    n = len(values)
    pad = 4
    vw = width - pad * 2
    vh = height - pad * 2
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(values):
        px = pad + (i / max(n - 1, 1)) * vw
        py = pad + vh - ((v - mn) / rng) * vh
        pts.append(f"{px:.1f},{py:.1f}")
    polyline = " ".join(pts)
    # Area fill
    area_pts = f"{pad},{pad + vh} {polyline} {pad + vw},{pad + vh}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="none"/>'
        f'<polygon points="{area_pts}" fill="{color}" opacity="0.1"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" r="2.5" fill="{color}"/>'
        f'</svg>'
    )


def bloom_chart_svg(questions: list, width: int = 280, height: int = 180) -> str:
    """Horizontal bar chart showing question count per Bloom taxonomy level."""
    counts = {level: 0 for level in BLOOM_LABELS}
    for q in questions:
        level = (q.get("bloom_level") or "").lower()
        if level in counts:
            counts[level] += 1
    max_count = max(counts.values()) or 1
    bar_h = 18
    gap = 6
    chart_top = 10
    label_w = 80
    bar_max_w = width - label_w - 20
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    for i, level in enumerate(BLOOM_LABELS):
        y = chart_top + i * (bar_h + gap)
        c = BLOOM_COLORS.get(level, "#94a3b8")
        cnt = counts[level]
        bar_w = max(2, int(cnt / max_count * bar_max_w))
        parts.append(f'<text x="{label_w - 4}" y="{y + bar_h - 4}" text-anchor="end" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="9" font-weight="500">{level}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{bar_w}" height="{bar_h}" rx="3" fill="{c}" opacity="0.85"/>')
        if bar_w > 20:
            parts.append(f'<text x="{label_w + 6}" y="{y + bar_h - 4}" fill="#fff" font-family="system-ui,sans-serif" font-size="9" font-weight="600">{cnt}</text>')
        else:
            parts.append(f'<text x="{label_w + bar_w + 4}" y="{y + bar_h - 4}" fill="{c}" font-family="system-ui,sans-serif" font-size="9" font-weight="600">{cnt}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def radar_svg(metrics: dict, width: int = 180, height: int = 180) -> str:
    """3-axis radar (triangle) for quality metrics: source_score, diversity, recency."""
    cx, cy = width // 2, height // 2
    radius = min(cx, cy) - 20
    # Three axes at 0°, 120°, 240°
    angles = [0, 120, 240]
    keys = ["avg_source_score", "source_diversity", "recency_score"]
    labels = ["Source Score", "Diversity", "Recency"]
    vals = []
    for k in keys:
        v = metrics.get(k, 0)
        if isinstance(v, (int, float)):
            vals.append(max(0.0, min(1.0, v)))
        else:
            vals.append(0.0)

    def pol(x, y):
        return f"{cx + radius * math.cos(math.radians(a)):.1f},{cy + radius * math.sin(math.radians(a)):.1f}"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    # Background triangles
    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for a in angles:
            r = radius * ring
            x = cx + r * math.cos(math.radians(a))
            y = cy + r * math.sin(math.radians(a))
            pts.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#2d2d4a" stroke-width="0.5" opacity="0.3"/>')
    # Axis lines
    for a, lbl in zip(angles, labels):
        x2 = cx + radius * math.cos(math.radians(a))
        y2 = cy + radius * math.sin(math.radians(a))
        lx = cx + (radius + 14) * math.cos(math.radians(a))
        ly = cy + (radius + 14) * math.sin(math.radians(a))
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#2d2d4a" stroke-width="0.5" opacity="0.4"/>')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    # Data triangle
    pts = []
    for a, v in zip(angles, vals):
        r = radius * v
        x = cx + r * math.cos(math.radians(a))
        y = cy + r * math.sin(math.radians(a))
        pts.append(f"{x:.1f},{y:.1f}")
    parts.append(f'<polygon points="{" ".join(pts)}" fill="#a855f7" opacity="0.2" stroke="#a855f7" stroke-width="1.5" stroke-linejoin="round"/>')
    for p in pts:
        parts.append(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3" fill="#a855f7"/>')
    # Center value labels
    for a, v in zip(angles, vals):
        r2 = radius * v * 0.6
        if r2 < 20:
            r2 = radius * v + 16
        lx = cx + r2 * math.cos(math.radians(a))
        ly = cy + r2 * math.sin(math.radians(a))
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" fill="#c084fc" font-family="system-ui,sans-serif" font-size="8" font-weight="600">{v:.2f}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def heatmap_svg(data: list[list[float]], row_labels: list[str] | None = None,
                col_labels: list[str] | None = None,
                cell_size: int = 28, gap: int = 2) -> str:
    """Simple grid heatmap. Values in [0,1] determine color intensity."""
    if not data or not data[0]:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"></svg>'
    rows = len(data)
    cols = len(data[0])
    label_w = 60 if row_labels else 0
    header_h = 16 if col_labels else 0
    w = label_w + cols * (cell_size + gap) + 4
    h = header_h + rows * (cell_size + gap) + 4
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="none"/>',
    ]
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            x = label_w + j * (cell_size + gap)
            y = header_h + i * (cell_size + gap)
            clamped = max(0.0, min(1.0, val))
            r = int(15 + clamped * 200)
            g = int(15 + (1 - clamped) * 200)
            fill = f"rgb({r},{g},{240 - int(clamped * 100)})"
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" fill="{fill}" opacity="0.85"/>')
            parts.append(f'<text x="{x + cell_size // 2}" y="{y + cell_size // 2 + 1}" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-family="system-ui,sans-serif" font-size="8" font-weight="600">{val:.1f}</text>')
    if row_labels:
        for i, lbl in enumerate(row_labels):
            y = header_h + i * (cell_size + gap) + cell_size // 2 + 1
            parts.append(f'<text x="{label_w - 4}" y="{y}" text-anchor="end" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    if col_labels:
        for j, lbl in enumerate(col_labels):
            x = label_w + j * (cell_size + gap) + cell_size // 2
            parts.append(f'<text x="{x}" y="{header_h - 4}" text-anchor="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{lbl}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def donut_svg(breakdown: dict, width: int = 140, height: int = 140) -> str:
    """Donut chart showing source proportions (HN, arXiv, PubMed)."""
    total = sum(breakdown.get(k, 0) for k in ("hn", "arxiv", "pubmed")) or 1
    cx, cy = width // 2, height // 2
    r = min(cx, cy) - 8
    inner_r = r * 0.6
    keys = [k for k in ("hn", "arxiv", "pubmed") if breakdown.get(k, 0) > 0]
    if not keys:
        keys = ["hn"]
    vals = [breakdown.get(k, 0) for k in keys]
    colors = [SOURCE_COLORS.get(k, "#94a3b8") for k in keys]
    # SVG arc helper: returns arc path from start_angle to end_angle
    def arc_path(cx, cy, r, a1, a2):
        a1r = math.radians(a1)
        a2r = math.radians(a2)
        x1 = cx + r * math.cos(a1r)
        y1 = cy + r * math.sin(a1r)
        x2 = cx + r * math.cos(a2r)
        y2 = cy + r * math.sin(a2r)
        large = 1 if (a2 - a1) > 180 else 0
        return f"M {cx},{cy} L {x1:.1f},{y1:.1f} A {r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="none"/>',
    ]
    start = 0
    for val, c in zip(vals, colors):
        angle = val / total * 360
        end = start + angle
        if angle > 0.5:
            parts.append(f'<path d="{arc_path(cx, cy, r, start, end)}" fill="{c}" opacity="0.85"/>')
        start = end

    # Inner circle (creates donut hole) with legend
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="var(--color-bg, #0f172a)"/>')
    parts.append(f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text, #e8e6e3)" font-family="system-ui,sans-serif" font-size="14" font-weight="700">{total}</text>')
    parts.append(f'<text x="{cx}" y="{cy + 12}" text-anchor="middle" dominant-baseline="middle" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="7">sources</text>')
    # Legend below
    ly = height - 12
    lx_start = 10
    lx = lx_start
    for key in ("hn", "arxiv", "pubmed"):
        val = breakdown.get(key, 0)
        if val <= 0:
            continue
        c = SOURCE_COLORS.get(key, "#94a3b8")
        parts.append(f'<rect x="{lx}" y="{ly - 4}" width="8" height="8" rx="1" fill="{c}"/>')
        parts.append(f'<text x="{lx + 10}" y="{ly + 2}" fill="var(--color-text-secondary, #475569)" font-family="system-ui,sans-serif" font-size="8">{SOURCE_LABELS.get(key, key)}</text>')
        lx += 50
    parts.append('</svg>')
    return "\n".join(parts)


def generate_sparkline_svg(data: list[float], pillar: str = "aml", width: int = 60, height: int = 24) -> str:
    """Generate an inline sparkline SVG for metadata cards."""
    from core.brand import brand_sparkline
    return brand_sparkline(data, pillar, width, height)
