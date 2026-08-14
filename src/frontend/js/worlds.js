const base_url = "http://localhost:8004" 

const worlds_list = document.getElementById('worlds_list');
const reload_worlds_btn = document.getElementById('reload_worlds_btn');



let user_id = null;
let is_admin = false;

async function init(){
    // console.log("start_init");
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();

    if(data.is_logged){
        user_id = data.user_id;
        is_admin = (data.is_admin=="1");
    }
    // console.log(data);
    // console.log(`inside init ${user_id} ${is_admin}`);
    // console.log("end_init");
}

async function check_world(world_id) {
    cookieStore.set("world_id", world_id);
    window.location.href = base_url + "/world";
}

async function change_visibility(world_id) {

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


async function render_worlds(){

    await init();

    const result = await fetch(base_url + "/api/v1/worlds/");
    const data = await result.json();

    worlds_list.innerHTML = '';

    // console.log("inside render");
    // console.log(wrld.user_id);
    // console.log(user_id);

    for(const wrld of data){
        var info = "";

        info += `world_id: ${wrld.world_id}\n`;
        info += `owner_id: ${wrld.user_id}\n`;
        info += `size: (${wrld.w},${wrld.h})\n`;
        info += `is_public: ${wrld.is_public}\n`;
        info += `seed: ${wrld.seed}`;

        const world_card = document.createElement('div');
        world_card.style = 'display: flex; margin: 10px; border: solid black 5px;';
        const txt_el = document.createElement('p');
        txt_el.textContent = info;

        
        if(wrld.user_id==user_id || is_admin){

            if(wrld.user_id==user_id){
                txt_el.textContent = "[yours] " + info;
            }
            
            const check_btn = document.createElement('button');
            check_btn.addEventListener('click', async () => {
                await check_world(wrld.world_id);
            });
            check_btn.textContent = 'check it out';

            const del_btn = document.createElement('button');
            del_btn.addEventListener('click', async () => {
                await del_world(wrld.world_id);
            });
            del_btn.textContent = 'delete world';
            
            const ch_vis_btn = document.createElement('button');
            ch_vis_btn.addEventListener('click', async () => {
                await change_visibility(wrld.world_id);
            });
            ch_vis_btn.textContent = 'change visibility';

            world_card.append(txt_el);
            world_card.append(check_btn);
            world_card.append(del_btn);
            world_card.append(ch_vis_btn);
            // console.log("owner");

        }
        else{
            if(wrld.is_public){
                const btn = document.createElement('button');
                btn.textContent = 'check it out';
                btn.addEventListener('click', async () => {
                    await check_world(wrld.world_id);
                });
                world_card.append(txt_el);
                world_card.append(btn);
            }
            else{
                world_card.append(txt_el);
            }
        }

        worlds_list.append(world_card);
        // console.log("###########");
    }
    
}


reload_worlds_btn.addEventListener('click', async () => { await render_worlds(); });

queueMicrotask(async ()=>{await init();});
queueMicrotask(async ()=>{await render_worlds();});


