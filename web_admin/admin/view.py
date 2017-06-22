# -*- coding: utf-8 -*-
# Created by zhangzhuo@360.cn on 17/6/20
from . import blueprint


@blueprint.route("/hi/", methods=['GET'], )
def hello():
    return "hello"


@blueprint.route("/", methods=['GET'], )
def index():
    debug_template = """
     <html>
       <head>
       </head>
       <body>
         <h1>Server sent events</h1>
         <div id="event"></div>
         <script type="text/javascript">

         var eventOutputContainer = document.getElementById("event");
         var evtSrc = new EventSource("/api/v1/pull/*.news");
         var evtSrc1 = new EventSource("/api/v1/stream/");

         evtSrc.onmessage = function(e) {
             console.log(e.data);
             eventOutputContainer.innerHTML = e.data;
         };
         
         evtSrc1.onmessage = function(e) {
             console.log(e.data);
             eventOutputContainer.innerHTML = e.data;
         };

         </script>
       </body>
     </html>
    """
    return (debug_template)
