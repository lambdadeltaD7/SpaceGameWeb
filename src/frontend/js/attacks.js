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
        return true;
    }
    else{
        alert("you must be logged in to do this");
        return false;
    }
}


async function attack_world(world_id) {
    cookieStore.set("attack_world_id", world_id);
    window.location.href = base_url + "/attack";
}


async function handle_world(wrld, txt_el, info, world_card, user_id){
    const attack_btn = document.createElement('button');
    attack_btn.type = 'button';
    attack_btn.className = 'attack-card-btn';
    attack_btn.addEventListener('click', async () => {
        await attack_world(wrld.world_id);
    });
    attack_btn.textContent = 'attack';

    const btn_container = document.createElement('div');
    btn_container.className = 'button-container';
    btn_container.append(attack_btn);

    world_card.append(txt_el);
    world_card.append(btn_container);
}

async function render_worlds(){
    const res = await init();

    if(res == false) return;

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
        world_card.className = 'attack-card';
        const txt_el = document.createElement('p');
        txt_el.className = 'attack-card-info';
        txt_el.textContent = info;

        if( (wrld.user_id != user_id) && wrld.is_public ){
            await handle_world(wrld, txt_el, info, world_card, user_id);
            worlds_list.append(world_card);
        }

        
    }
}


reload_worlds_btn.addEventListener('click', async () => { await render_worlds(); });

queueMicrotask(async () => {await init();});
queueMicrotask(async () => {await render_worlds();});

setInterval(async () => {await show_latest_transactions();}, 5000);