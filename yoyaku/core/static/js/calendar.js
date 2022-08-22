//
// 予約枠の状況を表すカレンダーを作成する
//

// 1桁の数字を0埋めで2桁にする
function toDoubleDigits(num) {
    num += "";
    if (num.length === 1) {
        num = "0" + num;
    }
    return num;
}
//　日時のフォーマットを"2020年1月1日 9:00〜"の用意する
function datetime_format(date) {
    var yyyy = date.getFullYear();
    var mm = date.getMonth() + 1;
    var dd = date.getDate();
    var hh = date.getHours();
    var mi = toDoubleDigits(date.getMinutes());
    return yyyy + '年' + mm + '月' + dd + '日 ' + hh + ':' + mi + '〜';
}

original = {
    initFullCalendar: function(slotMinTime, slotMaxTime) {
        document.addEventListener('DOMContentLoaded', function() {
            var calendarEl = document.getElementById('fullCalendar');
            $calendar = $('#fullCalendar');
            var today = new Date();
            var y = today.getFullYear();
            var m = today.getMonth();
            var d = today.getDate();
            var w = today.getDay();
            var period = 20;　 // 当日からの表示期間

            var end = new Date();
            end.setDate(end.getDate() + period);

            var calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'timeGridWeek',

                locale: 'ja',
                allDaySlot: false,
                slotMinTime: slotMinTime,
                slotMaxTime: slotMaxTime,
                initialDate: today,
                firstDay: w, // 一番左側の曜日は今日の曜日にする
                validRange: {
                    start: today,
                    end: end,
                },
                height: 1359,
                expandRows: true, //heightに応じて行の高さを自動調整
                defaultTimedEventDuration: '00:30',
                slotLabelFormat: {
                    hour: 'numeric',
                    minute: '2-digit',
                    omitZeroMinute: false,
                },
                droppable: false,
                events: [{
                        daysOfWeek: [0], //日曜日の背景色付け
                        display: "background",
                        color: "#F8E0E6",
                        allDay: true
                    },
                    {
                        daysOfWeek: [6], //土曜日の背景色付け
                        display: "background",
                        color: "#E0F2F7",
                        allDay: true
                    }
                ],

                eventClick: function(info) {
                    // 満席の予約枠を選択した場合は何もしない
                    if (info.event.title == "×") {
                        return;
                    }
                    // 値を取得
                    target_id = "id_booking_limit"
                    var element = document.getElementById(target_id);
                    const selelcted_id = element.value;
                    if (selelcted_id) {
                        old_event = calendar.getEventById(selelcted_id);
                        // selected_idのイベントを取得して背景色をリセット
                        old_event.setProp("backgroundColor", '#ffffff'); //白色
                        old_event.setProp("borderColor", old_event.textColor);
                    }
                    document.getElementById("selected_name").innerText = datetime_format(info.event.start);
                    document.getElementById("selected_name2").innerText = datetime_format(info.event.start);
                    element.value = info.event.id;
                    element.dataset.backgroundColor = info.event.backgroundColor;
                    element.dataset.borderColor = info.event.borderColor;

                    info.event.setProp("backgroundColor", '#ffea58'); // 黄色
                    info.event.setProp("borderColor", '#ff5c88'); // 赤色
                },
            });
            // 予約枠をカレンダーに追加
            var name = document.getElementsByName('hidden');
            var element = document.getElementById("id_booking_limit");
            const selelcted_id = element.value;

            name.forEach(element => {
                var start = new Date(Date.parse(element.dataset.startdatetime));
                var end = new Date(Date.parse(element.dataset.startdatetime));
                end.setMinutes(end.getMinutes() + 30); // 30分枠に固定
                var state = element.dataset.state;

                var textcolor = '';
                if (state == "●") {
                    textcolor = '#3c8dbc';
                } else if (state == "▲") {
                    textcolor = '#00a65a';
                } else if (state == "×") {
                    textcolor = '#999999';
                }

                backgroundColor ='#ffffff';
                borderColor = textcolor;
                
                // フォームエラーで再読み込みしたとき前回選択した予約枠があれば色付けする。
                if (element.id == selelcted_id){
                    backgroundColor = '#ffea58';
                    borderColor = '#ff5c88';
                }
                
                var event = {
                    id: element.id,
                    title: state,
                    start: start,
                    end: end,
                    textColor: textcolor,
                    backgroundColor: backgroundColor,
                    borderColor: borderColor,
                };
                calendar.addEvent(event);
            });

            calendar.render();

            // 再読み込みの場合選択した予約枠の開始日時を表示
            if (selelcted_id != ''){
                selected_event = calendar.getEventById(selelcted_id);
                document.getElementById("selected_name").innerText = datetime_format(selected_event.start);
                document.getElementById("selected_name2").innerText = datetime_format(selected_event.start);
            }

        });

    },
};