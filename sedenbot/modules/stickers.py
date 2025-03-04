# Copyright (C) 2020-2021 TeamDerUntergang <https://github.com/TeamDerUntergang>
#
# This file is part of TeamDerUntergang project,
# and licensed under GNU Affero General Public License v3.
# See the GNU Affero General Public License for more details.
#
# All rights reserved. See COPYING, AUTHORS.
#

from random import choice
from time import time

from PIL import Image
from pyrogram.errors import YouBlockedUser
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from sedenbot import HELP, PACKNAME, PACKNICK, TEMP_SETTINGS
from sedenecem.core import (
    PyroConversation,
    download_media_wc,
    edit,
    extract_args,
    get_download_dir,
    get_translation,
    reply_doc,
    sedenify,
)
from sedenecem.core import sticker_resize as resizer

# ================= CONSTANT =================
DIZCILIK = [get_translation(f'kangstr{i+1}') for i in range(0, 12)]
# ================= CONSTANT =================


@sedenify(pattern='^.(d[ıi]zla|kang)', compat=False)
def kang(client, message):
    myacc = TEMP_SETTINGS['ME']
    kanger = myacc.username or myacc.first_name
    if myacc.username:
        kanger = f'@{kanger}'
    args = extract_args(message)

    reply = message.reply_to_message
    if not reply:
        edit(message, f'`{get_translation("stickerUsage")}`')
        return

    anim = False
    media = None
    chat = 'Stickers'

    if reply.photo or reply.document or reply.sticker:
        edit(message, f'`{choice(DIZCILIK)}`')
        anim = reply.sticker and reply.sticker.is_animated
        media = download_media_wc(reply, sticker_orig=anim)
    else:
        edit(message, f'`{get_translation("stickerError")}`')
        return

    if not reply.sticker:
        try:
            media = resizer(media)
        except BaseException:
            edit(message, f'`{get_translation("stickerError")}`')
            return

    if len(args) < 1:
        args = '1'

    emoji = reply.sticker.emoji if reply.sticker and reply.sticker.emoji else '🤤'
    pack = 1

    for item in args.split():
        if item.isdigit():
            pack = int(item)
            args = args.replace(item, '').strip()
        else:
            emoji = args.strip()

    ptime = time()
    pname = f'PNAME_{ptime}'
    pnick = f'PNICK_{ptime}'

    name_suffix = ('_anim', ' (Animated)') if anim else ('', '')

    TEMP_SETTINGS[pname] = (
        PACKNAME.replace(' ', '')
        if PACKNAME
        else f'a{myacc.id}_by_{myacc.username}_{pack}{name_suffix[0]}'
    )
    TEMP_SETTINGS[f'{pname}_TEMPLATE'] = f'a{myacc.id}_by_{myacc.username}_'
    TEMP_SETTINGS[pnick] = (
        PACKNICK or f'{kanger}\'s UserBot pack {pack}{name_suffix[1]}'
    )
    TEMP_SETTINGS[f'{pnick}_TEMPLATE'] = f'{kanger}\'s UserBot pack '

    limit = '50' if anim else '120'

    def pack_created(pname):
        try:
            set_name = InputStickerSetShortName(short_name=TEMP_SETTINGS[pname])
            set = GetStickerSet(stickerset=set_name, hash=0)
            client.send(data=set)
            return True
        except BaseException:
            return False

    def create_new(conv, pack, pname, pnick):
        cmd = f'/new{"animated" if anim else "pack"}'

        try:
            send_recv(conv, cmd)
        except Exception as e:
            raise e
        msg = send_recv(conv, TEMP_SETTINGS[pnick])
        if 'Invalid pack selected.' in msg.text:
            pack += 1
            TEMP_SETTINGS[
                pname
            ] = f"{TEMP_SETTINGS[f'{pname}_TEMPLATE']}{pack}{name_suffix[0]}"
            TEMP_SETTINGS[
                pnick
            ] = f"{TEMP_SETTINGS[f'{pnick}_TEMPLATE']}{pack}{name_suffix[1]}"
            return create_new(conv, pack, pname, pnick)
        msg = send_recv(conv, media, doc=True)
        if 'Sorry' in msg.text:
            edit(message, f'`{get_translation("stickerError")}`')
            return
        send_recv(conv, emoji)
        send_recv(conv, '/publish')
        if anim:
            send_recv(conv, f'<{TEMP_SETTINGS[pnick]}>')
        send_recv(conv, '/skip')
        ret = send_recv(conv, TEMP_SETTINGS[pname])
        while 'already taken' in ret.text:
            pack += 1
            TEMP_SETTINGS[
                pname
            ] = f"{TEMP_SETTINGS[f'{pname}_TEMPLATE']}{pack}{name_suffix[0]}"
            TEMP_SETTINGS[
                pnick
            ] = f"{TEMP_SETTINGS[f'{pnick}_TEMPLATE']}{pack}{name_suffix[1]}"
            ret = send_recv(conv, TEMP_SETTINGS[pname])
        return True

    def add_exist(conv, pack, pname, pnick):
        try:
            send_recv(conv, '/addsticker')
        except Exception as e:
            raise e

        status = send_recv(conv, TEMP_SETTINGS[pname])

        if limit in status.text:
            pack += 1
            TEMP_SETTINGS[
                pname
            ] = f"{TEMP_SETTINGS[f'{pname}_TEMPLATE']}{pack}{name_suffix[0]}"
            TEMP_SETTINGS[
                pnick
            ] = f"{TEMP_SETTINGS[f'{pnick}_TEMPLATE']}{pack}{name_suffix[1]}"
            edit(message, get_translation('packFull', ['`', '**', str(pack)]))
            if pack_created(pname):
                return add_exist(conv, pack, pname, pnick)
            else:
                return create_new(conv, pack, pname, pnick)

        status = send_recv(conv, media, doc=True)
        if 'Sorry' in status.text:
            edit(message, f'`{get_translation("stickerError")}`')
            return
        send_recv(conv, emoji)
        send_recv(conv, '/done')
        return True

    with PyroConversation(client, chat) as conv:
        try:
            send_recv(conv, '/cancel')
        except YouBlockedUser:
            return edit(message, get_translation('unblockChat', ['**', '`', chat]))
        if pack_created(pname):
            ret = add_exist(conv, pack, pname, pnick)
            if not ret:
                return
        else:
            create_new(conv, pack, pname, pnick)

    edit(message, get_translation('stickerAdded', ['`', TEMP_SETTINGS[pname]]))
    del TEMP_SETTINGS[pname]
    del TEMP_SETTINGS[pnick]
    del TEMP_SETTINGS[f'{pname}_TEMPLATE']
    del TEMP_SETTINGS[f'{pnick}_TEMPLATE']


def send_recv(conv, msg, doc=False):
    if doc:
        conv.send_doc(msg)
    else:
        conv.send_msg(msg)
    return conv.recv_msg()


@sedenify(pattern='^.getsticker$')
def getsticker(message):
    reply = message.reply_to_message
    if not reply or not reply.sticker:
        edit(message, f'`{get_translation("replySticker")}`')
        return

    photo = download_media_wc(reply, f'{get_download_dir()}/sticker.png')
    image = Image.open(photo)
    photo = f'{get_download_dir()}/sticker.png'
    image.save(photo)

    reply_doc(
        reply,
        photo,
        caption=f'**Sticker ID:** `{reply.sticker.file_id}'
        f'`\n**Emoji**: `{reply.sticker.emoji or get_translation("notSet")}`',
        delete_after_send=True,
    )
    message.delete()


@sedenify(pattern='.packinfo$', compat=False)
def packinfo(client, message):
    reply = message.reply_to_message
    if not reply:
        edit(message, f'`{get_translation("packinfoError")}`')
        return

    if not reply.sticker:
        edit(message, f'`{get_translation("packinfoError2")}`')
        return

    edit(message, f'`{get_translation("processing")}`')

    get_stickerset = client.send(
        GetStickerSet(
            stickerset=InputStickerSetShortName(short_name=reply.sticker.set_name),
            hash=0,
        )
    )
    pack_emojis = []
    for document_sticker in get_stickerset.packs:
        if document_sticker.emoticon not in pack_emojis:
            pack_emojis.append(document_sticker.emoticon)

    out = get_translation(
        'packinfoResult',
        [
            '**',
            '`',
            get_stickerset.set.title,
            get_stickerset.set.short_name,
            get_stickerset.set.official,
            get_stickerset.set.archived,
            get_stickerset.set.animated,
            get_stickerset.set.count,
            ' '.join(pack_emojis),
        ],
    )

    edit(message, out)


HELP.update({'stickers': get_translation('stickerInfo')})
