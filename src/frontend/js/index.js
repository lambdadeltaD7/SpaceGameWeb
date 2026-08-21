import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const attack_btn = document.getElementById('attack_btn');

const login_button = document.getElementById('login_button');
const register_button = document.getElementById('register_button');
const logout_button = document.getElementById('logout_button');
const status_text = document.getElementById('status_text');

const online_info_text = document.getElementById('online_info_text');

const goto_transactions_btn = document.getElementById('goto_transactions_btn');

const worlds_btn = document.getElementById('worlds_btn');
const world_seed_input = document.getElementById('world_seed_input');
const world_gen_btn = document.getElementById('world_gen_btn');

const logout_wrap = document.getElementById('logout_wrap');
const gen_world_wrap = document.getElementById('gen_world_wrap');
const attack_wrap = document.getElementById('attack_wrap');
const login_wrap = document.getElementById('login_wrap');
const register_wrap = document.getElementById('register_wrap');
const transactions_wrap = document.getElementById('transactions_wrap');


const ONLINE_INFO_UPDATE_FREQ = 3000;
var user_id = null;


async function init(){
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();
   
    status_text.textContent = data.msg;   

    if(data.is_logged){
        login_button.style.display = "none";
        register_button.style.display = "none";
        logout_button.style.display = "block";
        world_seed_input.style.display = "block";
        world_gen_btn.style.display = "block";
        attack_btn.style.display = "block";
        logout_wrap.style.display = "flex";
        gen_world_wrap.style.display = "flex";
        attack_wrap.style.display = "flex";
        transactions_wrap.style.display = "flex";
        login_wrap.style.display = "none";
        register_wrap.style.display = "none";
        user_id = data.user_id;
    }
    else{
        login_wrap.style.display = "flex";
        register_wrap.style.display = "flex";
        login_button.style.display = "block";
        register_button.style.display = "block";
        logout_button.style.display = "none";
        world_seed_input.style.display = "none";
        world_gen_btn.style.display = "none";
        attack_btn.style.display = "none";
        logout_wrap.style.display = "none";
        gen_world_wrap.style.display = "none";
        attack_wrap.style.display = "none";
        transactions_wrap.style.display = "none";
    }

}


async function gen_world(){

    var params = new URLSearchParams({
            'user_id': user_id,
    });

    if(world_seed_input.value.length != 0){
        params.append('seed', world_seed_input.value);
    }
    
    const result = await fetch(
        base_url + `/api/v1/admin/generate_world?${params}`,
        {
            method: 'POST'
        }
    );


}


async function update_online_info(){
    const result = await fetch(base_url + "/api/v1/auth/online_info");
    const data = await result.json();
    online_info_text.textContent = `users_online: ${data.online_cnt} | users_logged: ${data.logged_cnt}`;
}


login_button.addEventListener('click', async () => {
    window.location.href = base_url + "/login";
});

register_button.addEventListener('click', async () => {
    window.location.href = base_url + "/registration";
});

logout_button.addEventListener('click', async () => {
    await fetch(base_url + "/api/v1/auth/logout");
    await init();
});

worlds_btn.addEventListener('click', async () => {
    window.location.href = base_url + "/worlds";
});

world_gen_btn.addEventListener('click', async () => {
    await gen_world();
});

goto_transactions_btn.addEventListener('click', () => {
    window.location.href = base_url + "/transactions";
});

attack_btn.addEventListener('click', () => {
    window.location.href = base_url + "/attacks";
});


queueMicrotask( async() => {await init();});
queueMicrotask( async() => {await update_online_info();});

setInterval(async () => {await update_online_info();}, ONLINE_INFO_UPDATE_FREQ);
setInterval(async () => {await show_latest_transactions();}, 5000);