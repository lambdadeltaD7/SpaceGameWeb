import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url,
    spreadImgOnBG
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
var update_status_block = false;
var constants = null;

function createDialog(id, title) {
    const dialog = document.createElement('div');
    dialog.id = id;
    dialog.className = 'dialog-overlay';
    dialog.dataset.dialogId = id;

    const content = document.createElement('div');
    content.className = 'dialog';

    if (title) {
        const header = document.createElement('div');
        header.className = 'dialog-header';
        header.textContent = title;
        content.append(header);
    }

    const text = document.createElement('div');
    text.className = 'dialog-text';
    content.append(text);

    const btn_container = document.createElement('div');
    btn_container.className = 'dialog-btn-container';
    content.append(btn_container);

    dialog.append(content);

    return { dialog, content, text, btn_container };
}

function createDialogButton(btn_text, is_secondary = false) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = is_secondary ? 'dialog-btn dialog-btn-secondary' : 'dialog-btn';
    btn.textContent = btn_text;
    return btn;
}

function closeDialog(dialog) {
    if (dialog) {
        dialog.remove();
    }
}

async function get_user_info_str() {
    const result = await fetch(base_url + `/api/v1/auth/session_info`);
    const data = await result.json();
    if (data.is_logged) {
        return ` username:${data.username}\n res1:${data.res1}\n res2:${data.res2}\n GLOBAL_cnt_active_shields:${data.cnt_active_shields}`;
    }
    else {
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
    world_id = await cookieStore.get('attack_world_id');
    world_id = world_id.value;

    const world_info = await get_world_info();
    curr_world_info = world_info;
    if(!update_status_block){
        world_info_txt.textContent = `
        owner_id: ${world_info.user_id}
        world_id: ${world_info.world_id} 
        seed: ${world_info.seed}
        size: (w,h) = (${world_info.w},${world_info.h})
        `;
        old_status_text = world_info_txt.textContent;
    }

    

    user_info_txt.textContent = await get_user_info_str();

    const planets = await get_world_planets();
    const miners = await get_world_miners();

    render_world(world_info, planets, miners);

    const res = await fetch(base_url + "/api/v1/admin/constants");
    constants = await res.json();
}

async function render_world(world_info, planets, miners) {
    const w = world_info.w;
    const h = world_info.h;

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
        curr_row.className = 'game-row';

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
        curr_cell.className = 'planet-cell';
        init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
    }

    else if (grid[i][j] == 2){
        curr_cell.className = 'planet-shield-cell';
        init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
    }

    else if (grid[i][j] == 3){
        curr_cell.className = 'miner-cell';
        init_miner_cell(curr_cell, m_dict[`${i}_${j}`]);
    }

    else{
        curr_cell.className = 'space-cell';
        init_space_cell(curr_cell, i, j);
    }

    return curr_cell;
}


function init_space_cell(curr_cell, i, j){
    curr_cell.className = 'space-cell';
}

function init_planet_cell(curr_cell, planet_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_planet(planet_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_planet);
    curr_cell.addEventListener('click', () => {on_mouse_click_planet(planet_info)});
}

function on_mouse_enter_planet(planet_info){
    update_status_block = true;
    world_info_txt.textContent = `
        planet_id = ${planet_info.planet_id},
        res1 = ${planet_info.res1},
        res2 = ${planet_info.res2},
        shield_on = ${planet_info.shield_on},
    `;

}

function on_mouse_leave_planet(){
    update_status_block = false;
    world_info_txt.textContent = old_status_text;
}

async function on_mouse_click_planet(planet_info){

    const { dialog, text, btn_container } = createDialog(
        `attack_planet_dialog_id_${planet_info.planet_id}`
    );

    text.textContent = `attack planet_id=${planet_info.planet_id}?\nit costs ${constants["PLANET_ATTACK_COST"]} res2\n`;

    const ok_btn = createDialogButton('attack planet');
    const cancel_btn = createDialogButton('cancel', true);

    btn_container.append(ok_btn, cancel_btn);

    ok_btn.addEventListener('click', async () => {
        await attack_planet_dialog_btn_ok_callable(dialog, planet_info);
    });

    cancel_btn.addEventListener('click', () => {
        closeDialog(dialog);
    });

    document.getElementById('doc_body').append(dialog);
}

function init_attack_planet_dialog(planet_info){
    return createDialog(`attack_planet_dialog_id_${planet_info.planet_id}`);
}

async function attack_planet_dialog_btn_ok_callable(dialog, planet_info){
    const result = await fetch(
    base_url + `/api/v1/planets/${planet_info.planet_id}/attack?world_id=${world_id}`,
        {
            method: 'DELETE',
        }
    );

    if(result.ok){
        closeDialog(dialog);
        await init();
    }
    else{
        const data = await result.json();
        showErr(data.detail);
        closeDialog(dialog);
    }
}


function init_miner_cell(curr_cell, miner_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_miner(miner_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_miner);
    curr_cell.addEventListener('click', () => {on_mouse_click_miner(miner_info)});
}

function on_mouse_enter_miner(miner_info){
    update_status_block = true;
    world_info_txt.textContent = `
        miner_id = ${miner_info.miner_id},
        x = ${miner_info.x},
        y = ${miner_info.y}
    `;

}

function on_mouse_leave_miner(){
    update_status_block = false;
    world_info_txt.textContent = old_status_text;
}

async function on_mouse_click_miner(miner_info){

    const { dialog, text, btn_container } = createDialog(
        `attack_miner_dialog_id_${miner_info.miner_id}`
    );

    text.textContent = `attack miner_id=${miner_info.miner_id}\nit costs ${constants["MINER_ATTACK_COST"]} res2\nconfirm?\n`;

    const ok_btn = createDialogButton('attack miner');
    const cancel_btn = createDialogButton('cancel', true);

    btn_container.append(ok_btn, cancel_btn);

    ok_btn.addEventListener('click', async () => {
        await attack_miner_dialog_btn_ok_callable(dialog, miner_info);
    });

    cancel_btn.addEventListener('click', () => {
        closeDialog(dialog);
    });

    document.getElementById('doc_body').append(dialog);
}

async function attack_miner_dialog_btn_ok_callable(dialog, miner_info){
    const result = await fetch(
        base_url + `/api/v1/miners/${miner_info.miner_id}/attack?world_id=${world_id}`,
            {
                method: 'DELETE',
            }
    );

    if(result.ok){
        closeDialog(dialog);
        await init();
    }
    else{
        const data = await result.json();
        showErr(data.detail);
        closeDialog(dialog);
    }
}


queueMicrotask(async () => {await init();});

setInterval(async () => {await show_latest_transactions();}, 5000);
setInterval(async () => {await init();}, 670);


spreadImgOnBG(128, '../img/star.png', 20, 6);
spreadImgOnBG(1, '../img/death_star.png', 512, 64);
spreadImgOnBG(20, '../img/ufo.png', 25, 10);