<!DOCTYPE html>
<html>
<head>
    <style type="text/css">
        body {
            background-color: #000;
            color: #ccc;
            font-family: Arial, Helvetica, sans-serif;
        }

        .stop {
            background-color: red;
        }

        .hide {
            display: none;
        }
    </style>
</head>
<body onload="init();">

    <input class='input' type="search" id="searchbox" placeholder="filter" tabindex="0" autofocus><br>
    <button onclick="stop()" id="stop" class="stop">stop</button>
    <div id="group-container">
        <?php
        function renderButtons($dir, &$results = array())
        {
            $files = scandir($dir);
            foreach ($files as $key => $value) {
                $path = $dir . DIRECTORY_SEPARATOR . $value;
                if (!is_dir($path)) {
                    $results[] = $path;
                    $title = str_replace("-", " ", $value);
                    $title = str_replace(".mp3", "", $title);
                    $title = str_replace(".wav", "", $title);
                    echo "<button onclick=\"play('$path')\" id=\"$value\" class=\"sample\">$title</button>\n";
                } else if ($value != "." && $value != "..") {
                    echo "<div class=\"button-container\">\n";
                    echo "<h3>$value</h3>";
                    renderButtons($path, $results);
                    $results[] = $path;
                }
            }
            return $results;
        }
        renderButtons('./audio');
        ?>
    </div>

    <script type="text/javascript">
        function play(fname) {
            var x = new Audio(fname);
            audioList.push(x);
            // TODO global vol control
            x.volume = 0.1;
            x.play()
        }

        function stop() {
            audioList.forEach(el => {
                el.pause();
            });
            audioList = [];
        }

        function cull() {
            // https://stackoverflow.com/questions/9437228/html5-check-if-audio-is-playing
        }

        function init() {
            init_search();
        }

        function init_search() {
            // https://css-tricks.com/in-page-filtered-search-with-vanilla-javascript/
            function search() {
                let cards = document.querySelectorAll('.sample')
                let search_query = document.getElementById("searchbox").value.toLowerCase();
                for (var i = 0; i < cards.length; i++) {
                    if (cards[i].innerText.toLowerCase().includes(search_query)) {
                        cards[i].classList.remove("hide");
                    } else {
                        cards[i].classList.add("hide");
                    }
                }
            }

            //A little delay
            let typingTimer;
            let typeInterval = 50;
            let searchInput = document.getElementById('searchbox');

            searchInput.addEventListener('keyup', () => {
                clearTimeout(typingTimer);
                typingTimer = setTimeout(search, typeInterval);
            });

        }
    </script>
</body>
</html>