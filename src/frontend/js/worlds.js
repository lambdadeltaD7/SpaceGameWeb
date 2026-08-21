import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const worlds_list = document.getElementById('worlds_list');
const reload_worlds_btn = document.getElementById('reload_worlds_btn');

let user_id = null;
let is_admin = false;


async function init(){
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();

    if(data.is_logged){
        user_id = data.user_id;
        is_admin = (data.is_admin=="1");
    }
}


async function checkout_world(world_id) {
    cookieStore.set("world_id", world_id);
    window.location.href = base_url + "/world";
}


async function change_world_visibility(world_id) {

    const r1 = await fetch(base_url + `/api/v1/worlds/${world_id}`);
    const wrld = await r1.json();

    const result = await fetch(
    base_url + `/api/v1/worlds/${world_id}?is_public=${!wrld.is_public}`,
        {
            method: 'PATCH',
        }
    );

    if(result.ok){
        await render_worlds();
    }
}


async function del_world(world_id) {
    const result = await fetch(
        base_url + `/api/v1/worlds/${world_id}`,
        {
            method: 'DELETE'
        }
    );

    if(result.ok){
        await render_worlds();
    }
}


async function case_authorized(wrld, txt_el, info, world_card, user_id){
    if(wrld.user_id==user_id){
        txt_el.textContent = "[yours] " + info;
    }

    const check_btn = document.createElement('button');
    check_btn.type = 'button';
    check_btn.className = 'world-card-btn';
    check_btn.addEventListener('click', async () => {
        await checkout_world(wrld.world_id);
    });
    check_btn.textContent = 'check it out';

    const del_btn = document.createElement('button');
    del_btn.type = 'button';
    del_btn.className = 'world-card-btn';
    del_btn.addEventListener('click', async () => {
        await del_world(wrld.world_id);
    });
    del_btn.textContent = 'delete world';

    const ch_vis_btn = document.createElement('button');
    ch_vis_btn.type = 'button';
    ch_vis_btn.className = 'world-card-btn';
    ch_vis_btn.addEventListener('click', async () => {
        await change_world_visibility(wrld.world_id);
    });
    ch_vis_btn.textContent = 'change visibility';

    const btn_container = document.createElement('div');
    btn_container.className = 'button-container';
    btn_container.append(check_btn, del_btn, ch_vis_btn);

    world_card.append(txt_el);
    world_card.append(btn_container);
}


async function case_not_authorized(wrld, txt_el, world_card){
    if(wrld.is_public){
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'world-card-btn';
        btn.textContent = 'check it out';
        btn.addEventListener('click', async () => {
            await checkout_world(wrld.world_id);
        });
        const btn_container = document.createElement('div');
        btn_container.className = 'button-container';
        btn_container.append(btn);
        world_card.append(txt_el);
        world_card.append(btn_container);
    }
    else{
        world_card.append(txt_el);
    }
}


async function render_worlds(){
    await init();

    const result = await fetch(base_url + "/api/v1/worlds/");
    const data = await result.json();

    worlds_list.innerHTML = '';

    for(const wrld of data){
        var info = "";
        info += `world_id: ${wrld.world_id}\n`;
        info += `owner_id: ${wrld.user_id}\n`;
        info += `size: (${wrld.w},${wrld.h})\n`;
        info += `is_public: ${wrld.is_public}\n`;
        info += `seed: ${wrld.seed}`;

        const world_card = document.createElement('div');
        world_card.className = 'world-card';
        const txt_el = document.createElement('p');
        txt_el.className = 'world-card-info';
        txt_el.textContent = info;

        if(wrld.user_id==user_id || is_admin){
            await case_authorized(wrld, txt_el, info, world_card, user_id);
        }
        else{
            await case_not_authorized(wrld, txt_el, world_card);
        }

        worlds_list.append(world_card);
    }
}


reload_worlds_btn.addEventListener('click', async () => { await render_worlds(); });

queueMicrotask(async () => {await init();});
queueMicrotask(async () => {await render_worlds();});

setInterval(async () => {await show_latest_transactions();}, 5000);