class ClearCheckBox {
    constructor(data) {
        this.data = data
        this.levelVar = 'level'
    }

    filterDataByClear() {
        const noPlayChecked = document.getElementById('clear-no_play').checked;
        const failedChecked = document.getElementById('clear-failed').checked;
        const easyChecked = document.getElementById('clear-easy').checked;
        const normalChecked = document.getElementById('clear-normal').checked;
        const hardChecked = document.getElementById('clear-hard').checked;
        const fcChecked = document.getElementById('clear-fc').checked;

        filteredData = data.filter(d => {
            if (d.status === 'NO PLAY' && noPlayChecked) return true;
            if (d.status === 'FAILED' && failedChecked) return true;
            if (d.status === 'EASY' && easyChecked) return true;
            if (d.status === 'NORMAL' && normalChecked) return true;
            if (d.status === 'HARD' && hardChecked) return true;
            if (d.status === 'FULL COMBO' && fcChecked) return true;
            return false;
        });
    }
}