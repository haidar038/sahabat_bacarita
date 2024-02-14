var socketio = io();

const chatContainer = document.getElementById("chatContainer");

const createMessage = (name, msg) => {
    const content = `
    {% for chats in chatContent %}
                                {% if chats.sender == current_user.username %}
                                <div class="text-end small text-muted">{{chats.sender}}</div>
                                <li class="chat-bubble-me rounded-start-5 rounded-bottom-5 p-3 mb-3 ms-auto">
                                    {{chats.pesan }}</li>
                                {% else %}
                                <div class="small text-muted">{{chats.sender}}</div>
                                <li class="chat-bubble-reply rounded-end-5 rounded-bottom-5 p-3 mb-3 me-auto">
                                    {{chats.pesan }}</li>
                                {% endif %}
                                {% endfor %}
let li = document.createElement("li");
            let chatRoom = document.querySelector("#chatRoom");

            // Memeriksa apakah pesan ditujukan untuk pengguna saat ini atau bukan
            if (data["username"] != "{{ current_user.username }}") {
                // Menampilkan pesan hanya jika sesuai dengan ruangan yang benar
                li.appendChild(document.createTextNode(data["message"]));
                li.classList.add("chat-bubble-reply", "rounded-end-pill", "rounded-bottom-pill", "p-3", "mb-3");
                chatContainer.appendChild(li);
                //if (data["room"] == "{{ current_user.room_id }}") {
                // }
    `;
    chatContainer.innerHTML += content;
};

socketio.on("message", (data) => {
    createMessage(data.name, data.message);
});

const sendMessage = () => {
    const message = document.getElementById("message");
    if (message.value == "") return;
    socketio.emit("message", { data: message.value });
    message.value = "";
};
