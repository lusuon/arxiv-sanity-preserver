
# arxiv sanity preserver

This project is a web interface that attempts to tame the overwhelming flood of papers on Arxiv. It allows researchers to keep track of recent papers, search for papers, sort papers by similarity to any paper, see recent popular papers, to add papers to a personal library, and to get personalized recommendations of (new or old) Arxiv papers. This code is currently running live at [www.arxiv-sanity.com/](http://www.arxiv-sanity.com/), where it's serving 25,000+ Arxiv papers from Machine Learning (cs.[CV|AI|CL|LG|NE]/stat.ML) over the last ~3 years. With this code base you could replicate the website to any of your favorite subsets of Arxiv by simply changing the categories in `fetch_papers.py`.

这个项目是一个试图揽取大量Arxiv上的论文的网络界面。 它允许研究人员跟踪最近的论文，搜索论文，通过与任何论文的相似性对论文进行分类，查看最近的热门论文，将论文添加到个人库，以及获得（新的或旧的）Arxiv论文的个性化推荐。 此代码目前正在[www.arxiv-sanity.com/](http://www.arxiv-sanity.com/)
上运行，它通过机器学习中提供过去3年内25,000多份Arxiv论文（cs.[CV | AI | CL | LG | NE] /stat.ML）。 使用此代码库，您只需更改`fetch_papers.py`中的类别，即可将网站复制到您最喜欢的Arxiv子集中。

![user interface](https://raw.github.com/karpathy/arxiv-sanity-preserver/master/ui.jpeg)

### Code layout 代码布局

There are two large parts of the code:有两大部分的代码：

**Indexing code**. Uses Arxiv API to download the most recent papers in any categories you like, and then downloads all papers, extracts all text, creates tfidf vectors based on the content of each paper. This code is therefore concerned with the backend scraping and computation: building up a database of arxiv papers, calculating content vectors, creating thumbnails, computing SVMs for people, etc.

**User interface**. Then there is a web server (based on Flask/Tornado/sqlite) that allows searching through the database and filtering papers by similarity, etc.

**索引代码**。 使用Arxiv API下载您喜欢的任何类别的最新论文，然后下载所有论文，提取所有文本，根据每篇论文的内容创建tfidf向量。 因此，此代码涉及后端抓取和计算：构建arxiv论文数据库，计算内容向量，创建缩略图，为人员计算SVM等。

**用户界面**。 然后有一个Web服务器（基于Flask / Tornado / sqlite），允许搜索数据库并通过相似性等过滤论文。

### Dependencies 依赖

Several: You will need numpy, feedparser (to process xml files), scikit learn (for tfidf vectorizer, training of SVM), flask (for serving the results), flask_limiter, and tornado (if you want to run the flask server in production). Also dateutil, and scipy. And sqlite3 for database (accounts, library support, etc.). Most of these are easy to get through `pip`, e.g.:

一些依赖：您将需要numpy，feedparser（处理xml文件），scikit learn（用于tfidf矢量化，SVM训练），flask（用于提供结果），flask_limiter和tornado（如果你想在生产中运行烧瓶服务器））。 还有dateutil和scipy。 和sqlite3用于数据库（帐户，库支持等）。 其中大多数都很容易通过`pip`安装，例如：

```bash
$ virtualenv env                # optional: use virtualenv
$ source env/bin/activate       # optional: use virtualenv
$ pip install -r requirements.txt
```

You will also need [ImageMagick](http://www.imagemagick.org/script/index.php) and [pdftotext](https://poppler.freedesktop.org/), which you can install on Ubuntu as `sudo apt-get install imagemagick poppler-utils`. Bleh, that's a lot of dependencies isn't it.

您还需要[ImageMagick]（http://www.imagemagick.org/script/index.php)和[pdftotext]（https://poppler.freedesktop.org/)，您可以在Ubuntu上安装为 `sudo apt-get install imagemagick poppler-utils`。 

### Processing pipeline 处理pineline

The processing pipeline requires you to run a series of scripts, and at this stage I really encourage you to manually inspect each script, as they may contain various inline settings you might want to change. In order, the processing pipeline is:

1. Run `fetch_papers.py` to query arxiv API and create a file `db.p` that contains all information for each paper. This script is where you would modify the **query**, indicating which parts of arxiv you'd like to use. Note that if you're trying to pull too many papers arxiv will start to rate limit you. You may have to run the script multiple times, and I recommend using the arg `--start-index` to restart where you left off when you were last interrupted by arxiv.
2. Run `download_pdfs.py`, which iterates over all papers in parsed pickle and downloads the papers into folder `pdf`
3. Run `parse_pdf_to_text.py` to export all text from pdfs to files in `txt`
4. Run `thumb_pdf.py` to export thumbnails of all pdfs to `thumb`
5. Run `analyze.py` to compute tfidf vectors for all documents based on bigrams. Saves a `tfidf.p`, `tfidf_meta.p` and `sim_dict.p` pickle files.
6. Run `buildsvm.py` to train SVMs for all users (if any), exports a pickle `user_sim.p`
7. Run `make_cache.py` for various preprocessing so that server starts faster (and make sure to run `sqlite3 as.db < schema.sql` if this is the very first time ever you're starting arxiv-sanity, which initializes an empty database).
8. Run the flask server with `serve.py`. Visit localhost:5000 and enjoy sane viewing of papers!

Optionally you can also run the `twitter_daemon.py` in a screen session, which uses your Twitter API credentials (stored in `twitter.txt`) to query Twitter periodically looking for mentions of papers in the database, and writes the results to the pickle file `twitter.p`.

I have a simple shell script that runs these commands one by one, and every day I run this script to fetch new papers, incorporate them into the database, and recompute all tfidf vectors/classifiers. More details on this process below.

**protip: numpy/BLAS**: The script `analyze.py` does quite a lot of heavy lifting with numpy. I recommend that you carefully set up your numpy to use BLAS (e.g. OpenBLAS), otherwise the computations will take a long time. With ~25,000 papers and ~5000 users the script runs in several hours on my current machine with a BLAS-linked numpy.

处理pineline要求您运行一系列脚本，在此阶段我真的鼓励您手动检查每个脚本，因为它们可能包含您可能想要更改的各种内联设置。按顺序，处理pineline是：

1.运行`fetch_papers.py`来查询arxiv API并创建一个包含每篇论文所有信息的文件`db.p`。您可以在此脚本中修改**查询**，指示您要使用的arxiv的哪些部分。请注意，如果你试图拉取太多论文，arxiv将开始限制你。您可能需要多次运行该脚本，当您上次被arxiv中断时，我建议使用arg` --start-index`，中断处继续重新启动。
2.运行`download_pdfs.py`，它遍历已解析的pickle中的所有文件，并将文件下载到文件夹`pdf`中。
3.运行`parse_pdf_to_text.py`将所有文本从pdfs导出到`txt`中的文件
4.运行`thumb_pdf.py`将所有pdf的缩略图导出到`thumb`
5.运行`analyze.py`，根据bigrams计算所有文档的tfidf向量。保存`tfidf.p`，`tfidf_meta.p`和`sim_dict.p` pickle文件。
6.运行`buildsvm.py`为所有用户（如果有的话）训练SVM，导出一个pickle`user_sim.p`
7.运行`make_cache.py`进行各种预处理，以便服务器启动更快（并确保运行`sqlite3 as.db <schema.sql`，如果这是你第一次启动arxiv-sanity，它初始化一个空的数据库）。
8.使用`serve.py`运行flask服务器。访问localhost：5000并享受论文！

您也可以选择在屏幕会话中运行`twitter_daemon.py`，它使用您的Twitter API凭据（存储在`twitter.txt`中）定期查询Twitter，查找数据库中的论文，并将结果写入pickle文件`twitter.p`。

我有一个简单的shell脚本，它逐个运行这些命令，每天我运行这个脚本来获取新文件，将它们合并到数据库中，并重新计算所有tfidf向量/分类器。有关此过程的更多详细信息如下：

** protip：numpy / BLAS **：脚本`analyze.py`在numpy中做了很多繁重的工作。我建议你仔细设置你的numpy使用BLAS（例如OpenBLAS），否则计算将花费很长时间。有大约25,000篇论文和大约5000个用户，脚本在我当前的机器上运行几个小时，并带有BLAS链接的numpy。

### Running online 上线运行

If you'd like to run the flask server online (e.g. AWS) run it as `python serve.py --prod`.

You also want to create a `secret_key.txt` file and fill it with random text (see top of `serve.py`).

如果您想在线运行flask服务器（例如AWS），请将其作为`python serve.py --prod`运行。

您还想创建一个`secret_key.txt`文件并用随机文本填充它（参见`serve.py`的顶部）。

### Current workflow 当前工作流程

Running the site live is not currently set up for a fully automatic plug and play operation. Instead it's a bit of a manual process and I thought I should document how I'm keeping this code alive right now. I have a script that performs the following update early morning after arxiv papers come out (~midnight PST):

目前尚未设置实时运行站点以进行全自动即插即用操作。 相反，这是一个手动过程，我想我应该记录我现在如何保持这些代码的存在。有一个在arxiv论文出来后执行以下更新的脚本：

```bash
python fetch_papers.py
python download_pdfs.py
python parse_pdf_to_text.py
python thumb_pdf.py
python analyze.py
python buildsvm.py
python make_cache.py
```

I run the server in a screen session, so `screen -S serve` to create it (or `-r` to reattach to it) and run:

我在屏幕会话中运行服务器，所以`screen -S serve`创建它（或`-r`重新连接到它）并运行：

```bash
python serve.py --prod --port 80
```

The server will load the new files and begin hosting the site. Note that on some systems you can't use port 80 without `sudo`. Your two options are to use `iptables` to reroute ports or you can use [setcap](http://stackoverflow.com/questions/413807/is-there-a-way-for-non-root-processes-to-bind-to-privileged-ports-1024-on-l) to elavate the permissions of your `python` interpreter that runs `serve.py`. In this case I'd recommend careful permissions and maybe virtualenv, etc.

服务器将加载新文件并开始托管该站点。 请注意，在某些系统上，如果没有“sudo”，则无法使用端口80。 有两个选择：使用`iptables`重新路由端口，或者你可以使用[setcap]（http://stackoverflow.com/questions/413807/is-there-a-way-for-non-root-processes-to- bind-to-privileged-ports-1024-on-l）以获得运行`serve.py`的`python`解释器的权限。 在这种情况下，我建议谨慎的权限，也许virtualenv等。
