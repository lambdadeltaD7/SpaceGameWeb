import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const status_bar = document.getElementById('status_bar');
const world_info_txt = document.getElementById('world_info_txt');
const user_info_txt = document.getElementById('user_info_txt');

const space = document.getElementById('space');
const game_grid = document.getElementById('game_grid');


var world_id = null;
var planet_info_card_id = null;
var old_status_text = null;
var curr_world_info = null;


async function get_user_info_str() {
    const result = await fetch(base_url + `/api/v1/auth/session_info`);
    const data = await result.json();
    if(data.is_logged){
        return `username:${data.username}, res1:${data.res1}, res2:${data.res2}, GLOBAL_cnt_active_shields:${data.cnt_active_shields}`;
    }
    else{
        return "You are not logged in. No info here."
    }
}

async function get_world_info() {
    const result = await fetch(base_url + `/api/v1/worlds/${world_id}`);
    const data = await result.json();
    return data;
}

async function get_world_planets() {
    const result = await fetch(base_url + `/api/v1/worlds/${world_id}/planets`);
    const data = await result.json();
    return data;
}

async function get_world_miners() {
    const result = await fetch(base_url + `/api/v1/worlds/${world_id}/miners`);
    const data = await result.json();
    return data;
}



async function init() {
    world_id = await cookieStore.get('world_id');
    world_id = world_id.value;

    const world_info = await get_world_info();
    curr_world_info = world_info;
    world_info_txt.textContent = `
    owner_id: ${world_info.user_id}
    world_id: ${world_info.world_id} 
    seed: ${world_info.seed}
    size: (w,h) = (${world_info.w},${world_info.h})
    `;

    old_status_text = world_info_txt.textContent;

    user_info_txt.textContent = await get_user_info_str();

    const planets = await get_world_planets();
    const miners = await get_world_miners();

    render_world(world_info, planets, miners);
}

async function render_world(world_info, planets, miners) {
    const w = world_info.w;
    const h = world_info.h;
    const cell_w = 100 / w;

    var grid = Array.from({length:h}, () => new Array(w).fill(0));
    var p_dict = {};
    var m_dict = {};
    
    for(var p of planets){
        grid[p.y][p.x] = 1;
        if(p.shield_on){
            grid[p.y][p.x] = 2;
        }
        p_dict[ `${p.y}_${p.x}` ] = p;
    }

    for(var m of miners){
        grid[m.y][m.x] = 3;
        m_dict[ `${m.y}_${m.x}` ] = m;
    }

    game_grid.innerHTML = '';
    for(var i=0; i<h; ++i){
        const curr_row = document.createElement('div');
        curr_row.style = "display: flex; flex-direction: row";

        for(var j=0; j<w; ++j){
            var curr_cell = render_cell(grid, p_dict, m_dict, i, j);
            curr_row.append(curr_cell);
        }

        game_grid.append(curr_row);
    }
}

function render_cell(grid, p_dict, m_dict, i, j){
    var curr_cell = document.createElement('div');

    if(grid[i][j] == 1){
        curr_cell.style.backgroundColor = "black";
        init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
    }

    else if (grid[i][j] == 2){
        curr_cell.style.backgroundColor = "green";
        init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
    }

    else if (grid[i][j] == 3){
        curr_cell.style.backgroundColor = "red";
        init_miner_cell(curr_cell, m_dict[`${i}_${j}`]);
    }

    else{
        curr_cell.style.backgroundColor = "blue";
        init_space_cell(curr_cell, i, j);
        curr_cell.className = 'space-cell';
    }
    
    curr_cell.style.width = `30px`;
    curr_cell.style.height = "30px";


    return curr_cell;
}



function init_space_cell(curr_cell, i, j){
    curr_cell.className = 'space-cell';
    curr_cell.addEventListener('click', () => {on_mouse_click_space(i, j)});
}



async function on_mouse_click_space(i, j){

    var add_miner_dialog = init_add_miner_dialog(i, j);
    const add_miner_dialog_btn_ok = document.createElement('button');
    const add_miner_dialog_btn_cancel = document.createElement('button');

    add_miner_dialog_btn_ok.textContent = 'add miner';
    add_miner_dialog_btn_cancel.textContent = 'cancel';

    add_miner_dialog.append(add_miner_dialog_btn_ok);
    add_miner_dialog.append(add_miner_dialog_btn_cancel);

    add_miner_dialog_btn_ok.addEventListener('click', async () => {
        await add_miner_dialog_btn_ok_callable(add_miner_dialog, i, j);
    });

    add_miner_dialog_btn_cancel.addEventListener('click', () => {
        add_miner_dialog.style.display = "none";
        document.getElementById(add_miner_dialog.id).remove();
    });

    document.getElementById('doc_body').append(add_miner_dialog);
}

function init_add_miner_dialog(i, j){
    var add_miner_dialog = document.createElement('div');
    add_miner_dialog.id = `add_miner_dialog_id_${world_id}_${i}_${j}`;
    
    add_miner_dialog.style =
        "position: absolute; top: 10%;" +
        "left: 30%; border: solid black 5px; flex-direction: column;" +
        "background-color: cadetblue; color: black;";

    const add_miner_dialog_txt = document.createElement('p');

    add_miner_dialog_txt.textContent = `do you want to add new miner to (x,y)=(${j},${i})?`;
    add_miner_dialog_txt.textContent += 'you will spend N res1!!!';
    add_miner_dialog.append(add_miner_dialog_txt);
   
    return add_miner_dialog;
}

async function add_miner_dialog_btn_ok_callable(add_miner_dialog, i, j){


    const miner_obj = {
        "world_id": world_id,
        "user_id": curr_world_info.user_id,
        "x" : j,
        "y" : i
    };
    
    console.log(`miner=${miner_obj}`);

    const result = await fetch(
        base_url + '/api/v1/miners/',
            {
                method: 'POST',
                headers:{
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(miner_obj)
            }
    );

    if(result.ok){
        document.getElementById(add_miner_dialog.id).style.display="none";
        document.getElementById(add_miner_dialog.id).remove();
        await init();
    }
    else{
        const data = await result.json();
        showErr(data.detail);
        document.getElementById(add_miner_dialog.id).remove();
    }
} 




function init_planet_cell(curr_cell, planet_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_planet(planet_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_planet);
    curr_cell.addEventListener('click', () => {on_mouse_click_planet(planet_info)});
}

function on_mouse_enter_planet(planet_info){
    world_info_txt.textContent = `
        planet_id = ${planet_info.planet_id},
        res1 = ${planet_info.res1},
        res2 = ${planet_info.res2},
        shield_on = ${planet_info.shield_on},
    `;

}

function on_mouse_leave_planet(){
    world_info_txt.textContent = old_status_text;
}

async function on_mouse_click_planet(planet_info){

    var shield_dialog = init_shield_dialog(planet_info);
    const shield_dialog_btn_ok = document.createElement('button');
    const shield_dialog_btn_cancel = document.createElement('button');

    shield_dialog_btn_ok.textContent = 'change shield status';
    shield_dialog_btn_cancel.textContent = 'cancel';

    shield_dialog.append(shield_dialog_btn_ok);
    shield_dialog.append(shield_dialog_btn_cancel);

    shield_dialog_btn_ok.addEventListener('click', async () => {
        await shield_dialog_btn_ok_callable(shield_dialog, planet_info);
    });

    shield_dialog_btn_cancel.addEventListener('click', () => {
        shield_dialog.style.display = "none";
        document.getElementById(shield_dialog.id).remove();
    });

    document.getElementById('doc_body').append(shield_dialog);
}

function init_shield_dialog(planet_info){
    var shield_dialog = document.createElement('div');
    shield_dialog.id = `shield_dialog_id_${planet_info.planet_id}`;
    
    shield_dialog.style =
        "position: absolute; top: 10%;" +
        "left: 30%; border: solid black 5px; flex-direction: column;" +
        "background-color: cadetblue; color: black;";

    const shield_dialog_txt = document.createElement('p');

    shield_dialog_txt.textContent = `shield menu for planet_id=${planet_info.planet_id}\n`;

    if(planet_info.shield_on){
        shield_dialog_txt.textContent += 'right now shield is active\n';
    }
    else{
        shield_dialog_txt.textContent += 'right now shield is NOT active\n';
    }
    shield_dialog_txt.textContent += 'when active shield consumes N res1 per sec\n';
    shield_dialog_txt.textContent += 'change shield status?\n';
    shield_dialog.append(shield_dialog_txt);
   

    return shield_dialog;
}

async function shield_dialog_btn_ok_callable(shield_dialog, planet_info){
    const result = await fetch(
    base_url + `/api/v1/planets/${planet_info.planet_id}?shield_on=${!planet_info.shield_on}`,
        {
            method: 'PATCH',
        }
    );

    if(result.ok){
        document.getElementById(shield_dialog.id).style.display="none";
        document.getElementById(shield_dialog.id).remove();
        await init();
    }
    else{
        const data = await result.json();
        showErr(data.detail);
        document.getElementById(shield_dialog.id).remove();
    }
} 



function init_miner_cell(curr_cell, miner_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_miner(miner_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_miner);
    curr_cell.addEventListener('click', () => {on_mouse_click_miner(miner_info)});
}

function on_mouse_enter_miner(miner_info){
    world_info_txt.textContent = `
        miner_id = ${miner_info.miner_id},
        x = ${miner_info.x},
        y = ${miner_info.y}
    `;

}

function on_mouse_leave_miner(){
    world_info_txt.textContent = old_status_text;
}

async function on_mouse_click_miner(miner_info){

    var sell_miner_dialog = init_sell_miner_dialog(miner_info);
    const sell_miner_dialog_btn_ok = document.createElement('button');
    const sell_miner_dialog_btn_cancel = document.createElement('button');

    sell_miner_dialog_btn_ok.textContent = 'sell miner';
    sell_miner_dialog_btn_cancel.textContent = 'cancel';

    sell_miner_dialog.append(sell_miner_dialog_btn_ok);
    sell_miner_dialog.append(sell_miner_dialog_btn_cancel);

    sell_miner_dialog_btn_ok.addEventListener('click', async () => {
        await sell_miner_dialog_btn_ok_callable(sell_miner_dialog, miner_info);
    });

    sell_miner_dialog_btn_cancel.addEventListener('click', () => {
        sell_miner_dialog.style.display = "none";
        document.getElementById(sell_miner_dialog.id).remove();
    });

    document.getElementById('doc_body').append(sell_miner_dialog);
}

function init_sell_miner_dialog(miner_info){
    var sell_miner_dialog = document.createElement('div');
    sell_miner_dialog.id = `sell_miner_dialog_id_${miner_info.miner_id}`;
    
    sell_miner_dialog.style =
        "position: absolute; top: 10%;" +
        "left: 30%; border: solid black 5px; flex-direction: column;" +
        "background-color: cadetblue; color: black;";

    const sell_miner_dialog_txt = document.createElement('p');

    sell_miner_dialog_txt.textContent = `sell miner_id=${miner_info.miner_id}\n`;
    sell_miner_dialog_txt.textContent += 'you will get half the buy price after it';
    sell_miner_dialog_txt.textContent += 'confirm?\n';

    sell_miner_dialog.append(sell_miner_dialog_txt);
   
    return sell_miner_dialog;
}

async function sell_miner_dialog_btn_ok_callable(sell_miner_dialog, miner_info){
    const result = await fetch(
    base_url + `/api/v1/miners/${miner_info.miner_id}`,
        {
            method: 'DELETE',
        }
    );

    if(result.ok){
        document.getElementById(sell_miner_dialog.id).style.display="none";
        document.getElementById(sell_miner_dialog.id).remove();
        await init();
    }
    else{
        const data = await result.json();
        showErr(data.detail);
        document.getElementById(sell_miner_dialog.id).remove();
    }
} 



queueMicrotask(async () => {await init();});

setInterval(async () => {await show_latest_transactions();}, 5000);
setInterval(async () => {await init();}, 670);