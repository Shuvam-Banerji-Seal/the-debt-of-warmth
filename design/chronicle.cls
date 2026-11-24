%% chronicle.cls — book design for the serial chronicle.
%% Designed by the orchestrator. The writer model must NOT edit this file;
%% it may only USE the public macros documented in design/AUTHOR-API.md.
%% Engine: LuaLaTeX. Compile from the repository root.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{design/chronicle}[2026/11/24 v1.0 Chronicle book design]
\LoadClass[11pt,twoside,openany]{book}
\@openrightfalse

\RequirePackage{iftex}
\RequireLuaTeX
\RequirePackage[paperwidth=6in,paperheight=9in,
  top=1.0in,bottom=0.98in,inner=0.9in,outer=0.84in,
  headheight=14pt,headsep=14pt,footskip=28pt]{geometry}
\RequirePackage[english]{babel}
\RequirePackage{fontspec}
\RequirePackage{xcolor,graphicx,eso-pic,etoolbox,xparse,calc,ifthen}
\RequirePackage{tikz}
\usetikzlibrary{calc,shapes,shapes.geometric,shapes.symbols,decorations.pathmorphing,
  decorations.pathreplacing,decorations.markings,decorations.text,patterns,fadings,
  shadows,arrows.meta,positioning,intersections,backgrounds}
\RequirePackage{pgfornament}
\RequirePackage[most]{tcolorbox}
\RequirePackage{lettrine}
\RequirePackage[noautomatic]{imakeidx}
\RequirePackage{titlesec,titletoc}
\RequirePackage{fancyhdr}
\RequirePackage[protrusion=true,expansion=true,tracking=true]{microtype}
\RequirePackage{multicol,enumitem,adjustbox,pdfpages,pdflscape,fmtcount,longtable,ragged2e,emptypage}
\RequirePackage[hidelinks,bookmarksnumbered,bookmarksopen]{hyperref}

%% ------------------------------------------------------------------ fonts
\directlua{
  luaotfload.add_fallback("chronfallback", {
    "file:NotoSerif-Regular.ttf:mode=node;",
    "file:FreeSerif.otf:mode=node;",
    "file:NotoSansSymbols-Regular.ttf:mode=node;",
    "file:NotoSansSymbols2-Regular.ttf:mode=node;",
  })
}
\setmainfont{EBGaramond}[
  Path=fonts/, Extension=.otf,
  UprightFont=*-Regular, ItalicFont=*-Italic,
  BoldFont=*-SemiBold, BoldItalicFont=*-SemiBoldItalic,
  Numbers=OldStyle, Ligatures={Common,TeX},
  RawFeature={fallback=chronfallback}]
\newfontfamily\CinzelFont{Cinzel}[Path=fonts/, Extension=.ttf,
  UprightFont=*-Regular, BoldFont=*-Bold, Ligatures=TeX,
  RawFeature={fallback=chronfallback}]
\newfontfamily\CinzelDeco{CinzelDecorative}[Path=fonts/, Extension=.ttf,
  UprightFont=*-Regular, BoldFont=*-Bold, Ligatures=TeX,
  RawFeature={fallback=chronfallback}]
\newfontfamily\FellFont{IMFeEN}[Path=fonts/, Extension=.otf,
  UprightFont=*rm28P, ItalicFont=*it28P, Ligatures={Common,TeX},
  RawFeature={fallback=chronfallback}]
\newfontfamily\FellSC{IMFeENsc28P}[Path=fonts/, Extension=.otf, Ligatures=TeX]
\newfontfamily\InitialsFont{EBGaramond-Initials}[Path=fonts/, Extension=.otf]

%% ----------------------------------------------------------------- colours
\definecolor{ink}{HTML}{2B1B0E}
\definecolor{rubric}{HTML}{7E1F14}
\definecolor{gold}{HTML}{9A7432}
\definecolor{faded}{HTML}{6E5B42}
\definecolor{blood}{HTML}{5C0B0B}
\definecolor{moss}{HTML}{4A5A2E}
\definecolor{night}{HTML}{1F2A3A}
\definecolor{ash}{HTML}{8C857B}
\definecolor{vellum}{HTML}{EFE2C4}
\colorlet{ornament}{gold!85!ink}
\AtBeginDocument{\color{ink}}

%% ------------------------------------------------------------ typography
\linespread{1.07}
\setlength{\parindent}{1.25em}
\setlength{\parskip}{0pt}
\raggedbottom
\widowpenalty=4000 \clubpenalty=4000
\emergencystretch=1.2em
\tolerance=1200

%% --------------------------------------------- page texture and border
%% Drawn once, stored as a reusable PDF form, stamped on every page.
\newif\ifCR@bgglobal \CR@bgglobaltrue
\newif\ifCR@bgpage   \CR@bgpagetrue
\newif\ifCR@bgplain  \CR@bgplainfalse
\newcommand\CRnobgthispage{\global\CR@bgpagefalse}
\newcommand\CRplainbgthispage{\global\CR@bgplaintrue}
\newcommand\CRbackgroundoff{\global\CR@bgglobalfalse}
\newcommand\CRbackgroundon{\global\CR@bgglobaltrue}
\newsavebox\CR@bgbox
\newcount\CR@bgindex
\newcount\CR@plainindex
\newcommand\CR@drawbackground{%
  \begin{tikzpicture}[x=\paperwidth,y=\paperheight]
    \useasboundingbox (0,0) rectangle (1,1);
    \node[inner sep=0pt,anchor=south west] at (0,0)
      {\includegraphics[width=\paperwidth,height=\paperheight]{design/textures/parchment.jpg}};
    \begin{scope}[x=1in,y=1in]
      \def\W{6}\def\H{9}
      \draw[ornament, line width=1.1pt] (0.30,0.30) rectangle (\W-0.30,\H-0.30);
      \draw[ornament!80, line width=0.35pt] (0.37,0.37) rectangle (\W-0.37,\H-0.37);
      \node[inner sep=0pt,anchor=north west] at (0.40,\H-0.40)
        {\pgfornament[width=0.52in,color=ornament]{61}};
      \node[inner sep=0pt,anchor=north east] at (\W-0.40,\H-0.40)
        {\pgfornament[width=0.52in,color=ornament,symmetry=v]{61}};
      \node[inner sep=0pt,anchor=south west] at (0.40,0.40)
        {\pgfornament[width=0.52in,color=ornament,symmetry=h]{61}};
      \node[inner sep=0pt,anchor=south east] at (\W-0.40,0.40)
        {\pgfornament[width=0.52in,color=ornament,symmetry=c]{61}};
    \end{scope}
  \end{tikzpicture}}
\AtBeginDocument{%
  \sbox\CR@bgbox{\CR@drawbackground}%
  \saveboxresource\CR@bgbox
  \global\CR@bgindex=\lastsavedboxresourceindex\relax
  \sbox\CR@bgbox{\includegraphics[width=\paperwidth,height=\paperheight]{design/textures/parchment.jpg}}%
  \saveboxresource\CR@bgbox
  \global\CR@plainindex=\lastsavedboxresourceindex\relax}
\AddToShipoutPictureBG{%
  \ifCR@bgglobal\ifCR@bgpage
    \ifCR@bgplain\put(0,0){\useboxresource\CR@plainindex}\else\put(0,0){\useboxresource\CR@bgindex}\fi
  \fi\fi}
\AddToHook{shipout/after}{\global\CR@bgpagetrue\global\CR@bgplainfalse}

%% ------------------------------------------------------ running heads
\newcommand\CR@booktitle{}
\newcommand\BookTitle[1]{\gdef\CR@booktitle{#1}}
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[CE]{\CinzelFont\footnotesize\addfontfeature{LetterSpace=12}\color{faded}\MakeUppercase{\CR@booktitle}}
\fancyhead[CO]{\FellFont\itshape\small\color{faded}\nouppercase{\leftmark}}
\fancyfoot[C]{\color{ornament}\raisebox{0.25ex}{\pgfornament[width=0.9em]{81}}%
  \enspace{\color{faded}\small\thepage}\enspace
  \raisebox{0.25ex}{\pgfornament[width=0.9em]{81}}}
\fancypagestyle{plain}{\fancyhf{}%
  \fancyfoot[C]{\color{faded}\small\thepage}}
\renewcommand{\chaptermark}[1]{\markboth{#1}{#1}}

%% ------------------------------------------------------ chapter heads
%% Per-chapter decoration (written by the author model) is set with
%% \CRdecoration{path} before \CRchapter; it is shrunk to fit its slot.
\newcommand\CR@defaultdeco{\pgfornament[width=0.62\textwidth,color=ornament]{69}}
\newcommand\CR@currentdeco{\CR@defaultdeco}
\newcommand\CRdecoration[1]{%
  \IfFileExists{#1}{\gdef\CR@currentdeco{\input{#1}}}{\gdef\CR@currentdeco{\CR@defaultdeco}}}
\newcommand\CR@decoslot{%
  \begingroup\color{ink}%
  \adjustbox{max width=\textwidth,max totalheight=1.45in}{\CR@currentdeco}%
  \endgroup\global\let\CR@currentdeco\CR@defaultdeco}
\newcommand\CR@chwhen{}\newcommand\CR@chwhere{}
\newcommand\CR@chapterafter{%
  \ifdefempty{\CR@chwhen}{}{%
    \par\vspace{6pt}{\FellFont\itshape\small\color{faded}\CR@chwhen
      \ifdefempty{\CR@chwhere}{}{\enspace\textperiodcentered\enspace\CR@chwhere}}}%
  \par\vspace{4pt}{\color{ornament}\pgfornament[width=0.42\textwidth]{88}}%
  \gdef\CR@chwhen{}\gdef\CR@chwhere{}}
\newcommand\CR@chapterlabel{%
  \CR@decoslot\par\vspace{8pt}%
  {\CinzelFont\footnotesize\addfontfeature{LetterSpace=30}\color{faded}CHAPTER}\par\vspace{1pt}%
  {\fontsize{30}{32}\selectfont\addfontfeature{Numbers=Lining}\color{rubric}\thechapter}}
\newcommand\CR@starredbefore{%
  {\color{ornament}\pgfornament[width=0.5\textwidth]{45}}\par\vspace{6pt}%
  \CinzelDeco\fontsize{20}{24}\selectfont\color{rubric}}
\newcommand\CR@starredafter{\par\vspace{4pt}{\color{ornament}\pgfornament[width=0.42\textwidth]{88}}}
\titleformat{\chapter}[display]
  {\centering\normalfont\color{ink}}
  {\CR@chapterlabel}
  {4pt}
  {\CinzelDeco\fontsize{19}{24}\selectfont\color{ink}}
  [\CR@chapterafter]
\titleformat{name=\chapter,numberless}[display]
  {\centering\normalfont\color{ink}}
  {}
  {0pt}
  {\CR@starredbefore}
  [\CR@starredafter]
\titlespacing*{\chapter}{0pt}{-12pt}{16pt}
\titleformat{\section}[block]{\centering\CinzelFont\large\color{rubric}}{}{0pt}{}
\titlespacing*{\section}{0pt}{14pt}{8pt}
\titleformat{\subsection}[block]{\FellFont\itshape\large\color{ink}}{}{0pt}{}
\titlespacing*{\subsection}{0pt}{10pt}{4pt}
\setcounter{secnumdepth}{0}

%% \CRchapter{number}{title}{when}{where}
\NewDocumentCommand\CRchapter{m m m m}{%
  \clearpage
  \setcounter{chapter}{\numexpr#1-1\relax}%
  \gdef\CR@chwhen{#3}\gdef\CR@chwhere{#4}%
  \chapter{#2}}

%% \CRepigraph{text}{attribution}
\NewDocumentCommand\CRepigraph{m m}{%
  \ifblank{#1}{}{%
  \begin{center}\begin{minipage}{0.78\textwidth}\centering
    {\FellFont\itshape\color{ink!85}#1\par}
    \ifblank{#2}{}{\vspace{3pt}{\FellSC\small\color{faded}--- #2\par}}
  \end{minipage}\end{center}\vspace{10pt}}}

%% Arc (part) pages: \CRarc{number}{title}{subtitle}
\NewDocumentCommand\CRarc{m m m}{%
  \clearpage\thispagestyle{empty}%
  \phantomsection\addcontentsline{toc}{part}{Arc \Numberstringnum{#1}: #2}%
  \vspace*{\fill}
  \begin{center}
    {\color{ornament}\pgfornament[width=0.62\textwidth]{69}}\par\vspace{18pt}
    {\CinzelFont\small\addfontfeature{LetterSpace=30}\color{faded}THE \MakeUppercase{\Ordinalstringnum{#1}} ARC}\par\vspace{10pt}
    {\CinzelDeco\fontsize{26}{32}\selectfont\color{rubric}#2}\par\vspace{10pt}
    \ifblank{#3}{}{{\FellFont\itshape\large\color{ink!85}#3}\par\vspace{12pt}}
    {\color{ornament}\pgfornament[width=0.5\textwidth]{75}}
  \end{center}
  \vspace*{\fill}\clearpage}

%% Scene break and tailpiece
\newcommand\scenebreak{\par\vspace{0.7\baselineskip}%
  {\centering\color{ornament}\pgfornament[width=2.6em]{11}\par}%
  \vspace{0.55\baselineskip}\noindent\ignorespaces}
\newcommand\CRtailpiece{\par\nopagebreak[4]\vspace{0.6\baselineskip}\nopagebreak[4]%
  {\centering\color{ornament}\pgfornament[width=0.22\textwidth]{72}\par}\vspace{0.3\baselineskip}}

%% Drop capital: \dropcap{W}{hen the rain}
\NewDocumentCommand\dropcap{m m}{%
  \lettrine[lines=3,lraise=0.06,loversize=0.06,findent=0.18em,nindent=0.12em]%
    {\color{rubric}\InitialsFont #1}{\scshape #2}}

%% In-prose devices the author may use
\newcommand\letterhand[1]{\begin{center}\begin{minipage}{0.86\textwidth}%
  \FellFont\itshape #1\end{minipage}\end{center}}
\newenvironment{verseblock}{\begin{center}\begin{minipage}{0.8\textwidth}\centering\FellFont\itshape}%
  {\end{minipage}\end{center}}
\newcommand\memory[1]{{\itshape #1}}
\newcommand\sound[1]{{\scshape #1}}
\newcommand\inscription[1]{{\CinzelFont\small\addfontfeature{LetterSpace=10}#1}}

%% -------------------------------------------------------- indexing
\makeindex[name=persons,title={Index of Persons},columns=2,options={-s design/chronicle.ist}]
\makeindex[name=places,title={Index of Places},columns=2,options={-s design/chronicle.ist}]
\makeindex[name=lore,title={Index of Lore, Powers \& Things},columns=2,options={-s design/chronicle.ist}]
\NewDocumentCommand\person{o m}{#2\IfValueTF{#1}{\index[persons]{#1}}{\index[persons]{#2}}}
\NewDocumentCommand\place{o m}{#2\IfValueTF{#1}{\index[places]{#1}}{\index[places]{#2}}}
\NewDocumentCommand\lore{o m}{#2\IfValueTF{#1}{\index[lore]{#1}}{\index[lore]{#2}}}
\newcommand\CRindexletter[1]{\par\vspace{6pt}{\centering\CinzelDeco\color{rubric}#1\par}\vspace{2pt}}
\indexsetup{level=\chapter*,toclevel=chapter,othercode={\small}}

%% ------------------------------------------------- chapter chronicle
\newtcolorbox{CRchroniclebox}[1]{enhanced,breakable,
  colback=gold!6!vellum,opacityback=0.45,colframe=ornament,
  boxrule=0.5pt,arc=1pt,left=9pt,right=9pt,top=8pt,bottom=6pt,
  before skip=16pt,after skip=10pt,
  fonttitle=\CinzelFont\footnotesize\addfontfeature{LetterSpace=15},
  coltitle=rubric,colbacktitle=vellum,
  attach boxed title to top center={yshift=-7pt},
  boxed title style={boxrule=0.5pt,colframe=ornament,arc=1pt},
  title={#1}}
\newenvironment{CRchronicle}[1]{%
  \begin{CRchroniclebox}{THE CHRONICLE OF CHAPTER #1}\small\setlength{\parindent}{1em}}%
  {\end{CRchroniclebox}}

%% ----------------------------------------------------- character pages
\newcommand\CRfield[2]{\par\noindent\hangindent=1.2em
  {\CinzelFont\scriptsize\addfontfeature{LetterSpace=10}\color{rubric}\MakeUppercase{#1}}\enspace{\small #2}\par\vspace{1pt}}
\newcommand\CR@portraitframe[1]{%
  \begin{tikzpicture}
    \node[inner sep=4pt] (p) {\adjustbox{max width=0.40\textwidth,max totalheight=2.5in}{\includegraphics{#1}}};
    \draw[ornament,line width=0.8pt] (p.south west) rectangle (p.north east);
    \draw[ornament,line width=0.3pt] ($(p.south west)+(2pt,2pt)$) rectangle ($(p.north east)-(2pt,2pt)$);
  \end{tikzpicture}}
%% \CRcharacter{name}{epithet}{portrait-file-or-empty}{fields}{body}
\NewDocumentCommand\CRcharacter{m m m +m +m}{%
  \clearpage
  \phantomsection\addcontentsline{toc}{section}{#1}%
  \begin{center}
    {\color{ornament}\pgfornament[width=0.45\textwidth]{46}}\par\vspace{4pt}
    {\CinzelDeco\fontsize{19}{23}\selectfont\color{rubric}#1}\par\vspace{2pt}
    \ifblank{#2}{}{{\FellFont\itshape\color{faded}#2}\par}
    \vspace{2pt}{\color{ornament}\pgfornament[width=0.45\textwidth]{88}}
  \end{center}
  \vspace{4pt}
  \ifblank{#3}{%
    \begin{minipage}{\textwidth}#4\end{minipage}}{%
    \noindent\begin{minipage}[t]{0.43\textwidth}\vspace{0pt}\CR@portraitframe{#3}\end{minipage}\hfill
    \begin{minipage}[t]{0.53\textwidth}\vspace{0pt}#4\end{minipage}}
  \par\vspace{10pt}
  #5\par}
\newcommand\CRsheetheading[1]{\par\vspace{7pt}{\centering\CinzelFont\small\addfontfeature{LetterSpace=12}\color{rubric}\MakeUppercase{#1}\par}\vspace{2pt}}

%% ------------------------------------------------------------- atlas
%% \CRmap{title}{image}{caption}   \CRmap*{...} rotates a landscape map
\NewDocumentCommand\CRmap{s m m +m}{%
  \clearpage
  \phantomsection\addcontentsline{toc}{section}{#2}%
  \begin{center}
    {\CinzelDeco\Large\color{rubric}#2}\par\vspace{6pt}
    \IfBooleanTF{#1}
      {\adjustbox{max width=\textwidth,max totalheight=0.80\textheight}{\includegraphics[angle=90]{#3}}}
      {\adjustbox{max width=\textwidth,max totalheight=0.80\textheight}{\includegraphics{#3}}}
    \par\vspace{6pt}
    \begin{minipage}{0.92\textwidth}\centering\FellFont\itshape\small #4\end{minipage}
  \end{center}}

%% ----------------------------------------------------------- timeline
\newenvironment{CRtimeline}{\begin{list}{}{\setlength{\leftmargin}{5.2em}
  \setlength{\labelwidth}{4.8em}\setlength{\labelsep}{0.4em}\setlength{\itemsep}{2pt}
  \setlength{\parsep}{0pt}\small}}{\end{list}}
\newcommand\CRday[2]{\item[{\CinzelFont\scriptsize\color{rubric}#1}]#2}

%% ------------------------------------------------------ generic prose
\newcommand\CRheading[1]{\CRsheetheading{#1}}
\newcommand\CRrule{\par{\centering\color{ornament}\pgfornament[width=0.3\textwidth]{88}\par}}

%% ------------------------------------------------------------- contents
\renewcommand\contentsname{The Chapters Herein}
\titlecontents{part}[0pt]{\addvspace{12pt}\centering\CinzelFont\small\color{rubric}}{}{}{}[\addvspace{4pt}]
\titlecontents{chapter}[2.4em]{\addvspace{2pt}\small}
  {\contentslabel[{\color{faded}\thecontentslabel}]{2.4em}}{}
  {\titlerule*[0.7pc]{\color{ash}.}\contentspage}
\titlecontents{section}[3.4em]{\footnotesize}{}{}{\titlerule*[0.7pc]{\color{ash}.}\contentspage}
\setcounter{tocdepth}{1}

%% ------------------------------------------------------- title pages
%% \CRtitlepage{title}{subtitle}{volume line}{volume title}{byline}
\NewDocumentCommand\CRtitlepage{m m m m m}{%
  \clearpage\thispagestyle{empty}\CRplainbgthispage
  \begin{tikzpicture}[remember picture,overlay]
    \node[anchor=north west,inner sep=0] at ($(current page.north west)+(0.48in,-0.48in)$)
      {\pgfornament[width=1.05in,color=ornament]{63}};
    \node[anchor=north east,inner sep=0] at ($(current page.north east)+(-0.48in,-0.48in)$)
      {\pgfornament[width=1.05in,color=ornament,symmetry=v]{63}};
    \node[anchor=south west,inner sep=0] at ($(current page.south west)+(0.48in,0.48in)$)
      {\pgfornament[width=1.05in,color=ornament,symmetry=h]{63}};
    \node[anchor=south east,inner sep=0] at ($(current page.south east)+(-0.48in,0.48in)$)
      {\pgfornament[width=1.05in,color=ornament,symmetry=c]{63}};
  \end{tikzpicture}%
  \vspace*{0.9in}
  \begin{center}
    {\CinzelDeco\fontsize{30}{36}\selectfont\color{rubric}#1}\par\vspace{10pt}
    \ifblank{#2}{}{{\FellFont\itshape\Large\color{ink!85}#2}\par\vspace{10pt}}
    {\color{ornament}\pgfornament[width=0.55\textwidth]{84}}\par\vspace{20pt}
    \ifblank{#3}{}{{\CinzelFont\addfontfeature{LetterSpace=20}\color{faded}\MakeUppercase{#3}}\par\vspace{6pt}}
    \ifblank{#4}{}{{\FellFont\itshape\large #4}\par}
    \vfill
    {\color{ornament}\pgfornament[width=0.35\textwidth]{65}}\par\vspace{10pt}
    {\FellSC\color{faded}#5}\par
  \end{center}
  \vspace*{0.5in}\clearpage}

\endinput
