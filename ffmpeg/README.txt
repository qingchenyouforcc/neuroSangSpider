FFmpeg 64-bit static Windows build from www.gyan.dev

Version: 2025-03-31-git-35c091f4b7-essentials_build-www.gyan.dev

License: GPL v3

Source Code: https://github.com/FFmpeg/FFmpeg/commit/35c091f4b7

git-essentials build configuration: 

ARCH                      x86 (generic)
big-endian                no
runtime cpu detection     yes
standalone assembly       yes
x86 assembler             nasm
MMX enabled               yes
MMXEXT enabled            yes
3DNow! enabled            yes
3DNow! extended enabled   yes
SSE enabled               yes
SSSE3 enabled             yes
AESNI enabled             yes
AVX enabled               yes
AVX2 enabled              yes
AVX-512 enabled           yes
AVX-512ICL enabled        yes
XOP enabled               yes
FMA3 enabled              yes
FMA4 enabled              yes
i686 features enabled     yes
CMOV is fast              yes
EBX available             yes
EBP available             yes
debug symbols             yes
strip symbols             yes
optimize for size         no
optimizations             yes
static                    yes
shared                    no
postprocessing support    yes
network support           yes
threading support         pthreads
safe bitstream reader     yes
texi2html enabled         no
perl enabled              yes
pod2man enabled           yes
makeinfo enabled          yes
makeinfo supports HTML    yes
xmllint enabled           yes

External libraries:
avisynth                libopencore_amrnb       libvpx
bzlib                   libopencore_amrwb       libwebp
gmp                     libopenjpeg             libx264
gnutls                  libopenmpt              libx265
iconv                   libopus                 libxml2
libaom                  librubberband           libxvid
libass                  libspeex                libzimg
libfontconfig           libsrt                  libzmq
libfreetype             libssh                  lzma
libfribidi              libtheora               mediafoundation
libgme                  libvidstab              sdl2
libgsm                  libvmaf                 zlib
libharfbuzz             libvo_amrwbenc
libmp3lame              libvorbis

External libraries providing hardware acceleration:
amf                     d3d12va                 nvdec
cuda                    dxva2                   nvenc
cuda_llvm               ffnvcodec               vaapi
cuvid                   libmfx
d3d11va                 libvpl

Libraries:
avcodec                 avformat                swresample
avdevice                avutil                  swscale
avfilter                postproc

Programs:
ffmpeg                  ffplay                  ffprobe

Enabled decoders:
aac                     fraps                   pgm
aac_fixed               frwu                    pgmyuv
aac_latm                ftr                     pgssub
aasc                    g2m                     pgx
ac3                     g723_1                  phm
ac3_fixed               g729                    photocd
acelp_kelvin            gdv                     pictor
adpcm_4xm               gem                     pixlet
adpcm_adx               gif                     pjs
adpcm_afc               gremlin_dpcm            png
adpcm_agm               gsm                     ppm
adpcm_aica              gsm_ms                  prores
adpcm_argo              h261                    prosumer
adpcm_ct                h263                    psd
adpcm_dtk               h263i                   ptx
adpcm_ea                h263p                   qcelp
adpcm_ea_maxis_xa       h264                    qdm2
adpcm_ea_r1             h264_amf                qdmc
adpcm_ea_r2             h264_cuvid              qdraw
adpcm_ea_r3             h264_qsv                qoa
adpcm_ea_xas            hap                     qoi
adpcm_g722              hca                     qpeg
adpcm_g726              hcom                    qtrle
adpcm_g726le            hdr                     r10k
adpcm_ima_acorn         hevc                    r210
adpcm_ima_alp           hevc_amf                ra_144
adpcm_ima_amv           hevc_cuvid              ra_288
adpcm_ima_apc           hevc_qsv                ralf
adpcm_ima_apm           hnm4_video              rasc
adpcm_ima_cunning       hq_hqa                  rawvideo
adpcm_ima_dat4          hqx                     realtext
adpcm_ima_dk3           huffyuv                 rka
adpcm_ima_dk4           hymt                    rl2
adpcm_ima_ea_eacs       iac                     roq
adpcm_ima_ea_sead       idcin                   roq_dpcm
adpcm_ima_iss           idf                     rpza
adpcm_ima_moflex        iff_ilbm                rscc
adpcm_ima_mtf           ilbc                    rtv1
adpcm_ima_oki           imc                     rv10
adpcm_ima_qt            imm4                    rv20
adpcm_ima_rad           imm5                    rv30
adpcm_ima_smjpeg        indeo2                  rv40
adpcm_ima_ssi           indeo3                  rv60
adpcm_ima_wav           indeo4                  s302m
adpcm_ima_ws            indeo5                  sami
adpcm_ima_xbox          interplay_acm           sanm
adpcm_ms                interplay_dpcm          sbc
adpcm_mtaf              interplay_video         scpr
adpcm_psx               ipu                     screenpresso
adpcm_sbpro_2           jacosub                 sdx2_dpcm
adpcm_sbpro_3           jpeg2000                sga
adpcm_sbpro_4           jpegls                  sgi
adpcm_swf               jv                      sgirle
adpcm_thp               kgv1                    sheervideo
adpcm_thp_le            kmvc                    shorten
adpcm_vima              lagarith                simbiosis_imx
adpcm_xa                lead                    sipr
adpcm_xmd               libaom_av1              siren
adpcm_yamaha            libgsm                  smackaud
adpcm_zork              libgsm_ms               smacker
agm                     libopencore_amrnb       smc
aic                     libopencore_amrwb       smvjpeg
alac                    libopus                 snow
alias_pix               libspeex                sol_dpcm
als                     libvorbis               sonic
amrnb                   libvpx_vp8              sp5x
amrwb                   libvpx_vp9              speedhq
amv                     loco                    speex
anm                     lscr                    srgc
ansi                    m101                    srt
anull                   mace3                   ssa
apac                    mace6                   stl
ape                     magicyuv                subrip
apng                    mdec                    subviewer
aptx                    media100                subviewer1
aptx_hd                 metasound               sunrast
arbc                    microdvd                svq1
argo                    mimic                   svq3
ass                     misc4                   tak
asv1                    mjpeg                   targa
asv2                    mjpeg_cuvid             targa_y216
atrac1                  mjpeg_qsv               tdsc
atrac3                  mjpegb                  text
atrac3al                mlp                     theora
atrac3p                 mmvideo                 thp
atrac3pal               mobiclip                tiertexseqvideo
atrac9                  motionpixels            tiff
aura                    movtext                 tmv
aura2                   mp1                     truehd
av1                     mp1float                truemotion1
av1_amf                 mp2                     truemotion2
av1_cuvid               mp2float                truemotion2rt
av1_qsv                 mp3                     truespeech
avrn                    mp3adu                  tscc
avrp                    mp3adufloat             tscc2
avs                     mp3float                tta
avui                    mp3on4                  twinvq
bethsoftvid             mp3on4float             txd
bfi                     mpc7                    ulti
bink                    mpc8                    utvideo
binkaudio_dct           mpeg1_cuvid             v210
binkaudio_rdft          mpeg1video              v210x
bintext                 mpeg2_cuvid             v308
bitpacked               mpeg2_qsv               v408
bmp                     mpeg2video              v410
bmv_audio               mpeg4                   vb
bmv_video               mpeg4_cuvid             vble
bonk                    mpegvideo               vbn
brender_pix             mpl2                    vc1
c93                     msa1                    vc1_cuvid
cavs                    mscc                    vc1_qsv
cbd2_dpcm               msmpeg4v1               vc1image
ccaption                msmpeg4v2               vcr1
cdgraphics              msmpeg4v3               vmdaudio
cdtoons                 msnsiren                vmdvideo
cdxl                    msp2                    vmix
cfhd                    msrle                   vmnc
cinepak                 mss1                    vnull
clearvideo              mss2                    vorbis
cljr                    msvideo1                vp3
cllc                    mszh                    vp4
comfortnoise            mts2                    vp5
cook                    mv30                    vp6
cpia                    mvc1                    vp6a
cri                     mvc2                    vp6f
cscd                    mvdv                    vp7
cyuv                    mvha                    vp8
dca                     mwsc                    vp8_cuvid
dds                     mxpeg                   vp8_qsv
derf_dpcm               nellymoser              vp9
dfa                     notchlc                 vp9_cuvid
dfpwm                   nuv                     vp9_qsv
dirac                   on2avc                  vplayer
dnxhd                   opus                    vqa
dolby_e                 osq                     vqc
dpx                     paf_audio               vvc
dsd_lsbf                paf_video               vvc_qsv
dsd_lsbf_planar         pam                     wady_dpcm
dsd_msbf                pbm                     wavarc
dsd_msbf_planar         pcm_alaw                wavpack
dsicinaudio             pcm_bluray              wbmp
dsicinvideo             pcm_dvd                 wcmv
dss_sp                  pcm_f16le               webp
dst                     pcm_f24le               webvtt
dvaudio                 pcm_f32be               wmalossless
dvbsub                  pcm_f32le               wmapro
dvdsub                  pcm_f64be               wmav1
dvvideo                 pcm_f64le               wmav2
dxa                     pcm_lxf                 wmavoice
dxtory                  pcm_mulaw               wmv1
dxv                     pcm_s16be               wmv2
eac3                    pcm_s16be_planar        wmv3
eacmv                   pcm_s16le               wmv3image
eamad                   pcm_s16le_planar        wnv1
eatgq                   pcm_s24be               wrapped_avframe
eatgv                   pcm_s24daud             ws_snd1
eatqi                   pcm_s24le               xan_dpcm
eightbps                pcm_s24le_planar        xan_wc3
eightsvx_exp            pcm_s32be               xan_wc4
eightsvx_fib            pcm_s32le               xbin
escape124               pcm_s32le_planar        xbm
escape130               pcm_s64be               xface
evrc                    pcm_s64le               xl
exr                     pcm_s8                  xma1
fastaudio               pcm_s8_planar           xma2
ffv1                    pcm_sga                 xpm
ffvhuff                 pcm_u16be               xsub
ffwavesynth             pcm_u16le               xwd
fic                     pcm_u24be               y41p
fits                    pcm_u24le               ylc
flac                    pcm_u32be               yop
flashsv                 pcm_u32le               yuv4
flashsv2                pcm_u8                  zero12v
flic                    pcm_vidc                zerocodec
flv                     pcx                     zlib
fmvc                    pdv                     zmbv
fourxm                  pfm

Enabled encoders:
a64multi                hevc_d3d12va            pcm_u16le
a64multi5               hevc_mf                 pcm_u24be
aac                     hevc_nvenc              pcm_u24le
aac_mf                  hevc_qsv                pcm_u32be
ac3                     hevc_vaapi              pcm_u32le
ac3_fixed               huffyuv                 pcm_u8
ac3_mf                  jpeg2000                pcm_vidc
adpcm_adx               jpegls                  pcx
adpcm_argo              libaom_av1              pfm
adpcm_g722              libgsm                  pgm
adpcm_g726              libgsm_ms               pgmyuv
adpcm_g726le            libmp3lame              phm
adpcm_ima_alp           libopencore_amrnb       png
adpcm_ima_amv           libopenjpeg             ppm
adpcm_ima_apm           libopus                 prores
adpcm_ima_qt            libspeex                prores_aw
adpcm_ima_ssi           libtheora               prores_ks
adpcm_ima_wav           libvo_amrwbenc          qoi
adpcm_ima_ws            libvorbis               qtrle
adpcm_ms                libvpx_vp8              r10k
adpcm_swf               libvpx_vp9              r210
adpcm_yamaha            libwebp                 ra_144
alac                    libwebp_anim            rawvideo
alias_pix               libx264                 roq
amv                     libx264rgb              roq_dpcm
anull                   libx265                 rpza
apng                    libxvid                 rv10
aptx                    ljpeg                   rv20
aptx_hd                 magicyuv                s302m
ass                     mjpeg                   sbc
asv1                    mjpeg_qsv               sgi
asv2                    mjpeg_vaapi             smc
av1_amf                 mlp                     snow
av1_mf                  movtext                 speedhq
av1_nvenc               mp2                     srt
av1_qsv                 mp2fixed                ssa
av1_vaapi               mp3_mf                  subrip
avrp                    mpeg1video              sunrast
avui                    mpeg2_qsv               svq1
bitpacked               mpeg2_vaapi             targa
bmp                     mpeg2video              text
cfhd                    mpeg4                   tiff
cinepak                 msmpeg4v2               truehd
cljr                    msmpeg4v3               tta
comfortnoise            msrle                   ttml
dca                     msvideo1                utvideo
dfpwm                   nellymoser              v210
dnxhd                   opus                    v308
dpx                     pam                     v408
dvbsub                  pbm                     v410
dvdsub                  pcm_alaw                vbn
dvvideo                 pcm_bluray              vc2
dxv                     pcm_dvd                 vnull
eac3                    pcm_f32be               vorbis
exr                     pcm_f32le               vp8_vaapi
ffv1                    pcm_f64be               vp9_qsv
ffvhuff                 pcm_f64le               vp9_vaapi
fits                    pcm_mulaw               wavpack
flac                    pcm_s16be               wbmp
flashsv                 pcm_s16be_planar        webvtt
flashsv2                pcm_s16le               wmav1
flv                     pcm_s16le_planar        wmav2
g723_1                  pcm_s24be               wmv1
gif                     pcm_s24daud             wmv2
h261                    pcm_s24le               wrapped_avframe
h263                    pcm_s24le_planar        xbm
h263p                   pcm_s32be               xface
h264_amf                pcm_s32le               xsub
h264_mf                 pcm_s32le_planar        xwd
h264_nvenc              pcm_s64be               y41p
h264_qsv                pcm_s64le               yuv4
h264_vaapi              pcm_s8                  zlib
hdr                     pcm_s8_planar           zmbv
hevc_amf                pcm_u16be

Enabled hwaccels:
av1_d3d11va             hevc_nvdec              vc1_nvdec
av1_d3d11va2            hevc_vaapi              vc1_vaapi
av1_d3d12va             mjpeg_nvdec             vp8_nvdec
av1_dxva2               mjpeg_vaapi             vp8_vaapi
av1_nvdec               mpeg1_nvdec             vp9_d3d11va
av1_vaapi               mpeg2_d3d11va           vp9_d3d11va2
h263_vaapi              mpeg2_d3d11va2          vp9_d3d12va
h264_d3d11va            mpeg2_d3d12va           vp9_dxva2
h264_d3d11va2           mpeg2_dxva2             vp9_nvdec
h264_d3d12va            mpeg2_nvdec             vp9_vaapi
h264_dxva2              mpeg2_vaapi             vvc_vaapi
h264_nvdec              mpeg4_nvdec             wmv3_d3d11va
h264_vaapi              mpeg4_vaapi             wmv3_d3d11va2
hevc_d3d11va            vc1_d3d11va             wmv3_d3d12va
hevc_d3d11va2           vc1_d3d11va2            wmv3_dxva2
hevc_d3d12va            vc1_d3d12va             wmv3_nvdec
hevc_dxva2              vc1_dxva2               wmv3_vaapi

Enabled parsers:
aac                     dvdsub                  mpegaudio
aac_latm                evc                     mpegvideo
ac3                     ffv1                    opus
adx                     flac                    png
amr                     ftr                     pnm
av1                     g723_1                  qoi
avs2                    g729                    rv34
avs3                    gif                     sbc
bmp                     gsm                     sipr
cavsvideo               h261                    tak
cook                    h263                    vc1
cri                     h264                    vorbis
dca                     hdr                     vp3
dirac                   hevc                    vp8
dnxhd                   ipu                     vp9
dnxuc                   jpeg2000                vvc
dolby_e                 jpegxl                  webp
dpx                     misc4                   xbm
dvaudio                 mjpeg                   xma
dvbsub                  mlp                     xwd
dvd_nav                 mpeg4video

Enabled demuxers:
aa                      idf                     pcm_mulaw
aac                     iff                     pcm_s16be
aax                     ifv                     pcm_s16le
ac3                     ilbc                    pcm_s24be
ac4                     image2                  pcm_s24le
ace                     image2_alias_pix        pcm_s32be
acm                     image2_brender_pix      pcm_s32le
act                     image2pipe              pcm_s8
adf                     image_bmp_pipe          pcm_u16be
adp                     image_cri_pipe          pcm_u16le
ads                     image_dds_pipe          pcm_u24be
adx                     image_dpx_pipe          pcm_u24le
aea                     image_exr_pipe          pcm_u32be
afc                     image_gem_pipe          pcm_u32le
aiff                    image_gif_pipe          pcm_u8
aix                     image_hdr_pipe          pcm_vidc
alp                     image_j2k_pipe          pdv
amr                     image_jpeg_pipe         pjs
amrnb                   image_jpegls_pipe       pmp
amrwb                   image_jpegxl_pipe       pp_bnk
anm                     image_pam_pipe          pva
apac                    image_pbm_pipe          pvf
apc                     image_pcx_pipe          qcp
ape                     image_pfm_pipe          qoa
apm                     image_pgm_pipe          r3d
apng                    image_pgmyuv_pipe       rawvideo
aptx                    image_pgx_pipe          rcwt
aptx_hd                 image_phm_pipe          realtext
aqtitle                 image_photocd_pipe      redspark
argo_asf                image_pictor_pipe       rka
argo_brp                image_png_pipe          rl2
argo_cvg                image_ppm_pipe          rm
asf                     image_psd_pipe          roq
asf_o                   image_qdraw_pipe        rpl
ass                     image_qoi_pipe          rsd
ast                     image_sgi_pipe          rso
au                      image_sunrast_pipe      rtp
av1                     image_svg_pipe          rtsp
avi                     image_tiff_pipe         s337m
avisynth                image_vbn_pipe          sami
avr                     image_webp_pipe         sap
avs                     image_xbm_pipe          sbc
avs2                    image_xpm_pipe          sbg
avs3                    image_xwd_pipe          scc
bethsoftvid             imf                     scd
bfi                     ingenient               sdns
bfstm                   ipmovie                 sdp
bink                    ipu                     sdr2
binka                   ircam                   sds
bintext                 iss                     sdx
bit                     iv8                     segafilm
bitpacked               ivf                     ser
bmv                     ivr                     sga
boa                     jacosub                 shorten
bonk                    jpegxl_anim             siff
brstm                   jv                      simbiosis_imx
c93                     kux                     sln
caf                     kvag                    smacker
cavsvideo               laf                     smjpeg
cdg                     lc3                     smush
cdxl                    libgme                  sol
cine                    libopenmpt              sox
codec2                  live_flv                spdif
codec2raw               lmlm4                   srt
concat                  loas                    stl
dash                    lrc                     str
data                    luodat                  subviewer
daud                    lvf                     subviewer1
dcstr                   lxf                     sup
derf                    m4v                     svag
dfa                     matroska                svs
dfpwm                   mca                     swf
dhav                    mcc                     tak
dirac                   mgsts                   tedcaptions
dnxhd                   microdvd                thp
dsf                     mjpeg                   threedostr
dsicin                  mjpeg_2000              tiertexseq
dss                     mlp                     tmv
dts                     mlv                     truehd
dtshd                   mm                      tta
dv                      mmf                     tty
dvbsub                  mods                    txd
dvbtxt                  moflex                  ty
dxa                     mov                     usm
ea                      mp3                     v210
ea_cdata                mpc                     v210x
eac3                    mpc8                    vag
epaf                    mpegps                  vc1
evc                     mpegts                  vc1t
ffmetadata              mpegtsraw               vividas
filmstrip               mpegvideo               vivo
fits                    mpjpeg                  vmd
flac                    mpl2                    vobsub
flic                    mpsub                   voc
flv                     msf                     vpk
fourxm                  msnwc_tcp               vplayer
frm                     msp                     vqf
fsb                     mtaf                    vvc
fwse                    mtv                     w64
g722                    musx                    wady
g723_1                  mv                      wav
g726                    mvi                     wavarc
g726le                  mxf                     wc3
g729                    mxg                     webm_dash_manifest
gdv                     nc                      webvtt
genh                    nistsphere              wsaud
gif                     nsp                     wsd
gsm                     nsv                     wsvqa
gxf                     nut                     wtv
h261                    nuv                     wv
h263                    obu                     wve
h264                    ogg                     xa
hca                     oma                     xbin
hcom                    osq                     xmd
hevc                    paf                     xmv
hls                     pcm_alaw                xvag
hnm                     pcm_f32be               xwma
iamf                    pcm_f32le               yop
ico                     pcm_f64be               yuv4mpegpipe
idcin                   pcm_f64le

Enabled muxers:
a64                     h263                    pcm_s16le
ac3                     h264                    pcm_s24be
ac4                     hash                    pcm_s24le
adts                    hds                     pcm_s32be
adx                     hevc                    pcm_s32le
aea                     hls                     pcm_s8
aiff                    iamf                    pcm_u16be
alp                     ico                     pcm_u16le
amr                     ilbc                    pcm_u24be
amv                     image2                  pcm_u24le
apm                     image2pipe              pcm_u32be
apng                    ipod                    pcm_u32le
aptx                    ircam                   pcm_u8
aptx_hd                 ismv                    pcm_vidc
argo_asf                ivf                     psp
argo_cvg                jacosub                 rawvideo
asf                     kvag                    rcwt
asf_stream              latm                    rm
ass                     lc3                     roq
ast                     lrc                     rso
au                      m4v                     rtp
avi                     matroska                rtp_mpegts
avif                    matroska_audio          rtsp
avm2                    md5                     sap
avs2                    microdvd                sbc
avs3                    mjpeg                   scc
bit                     mkvtimestamp_v2         segafilm
caf                     mlp                     segment
cavsvideo               mmf                     smjpeg
codec2                  mov                     smoothstreaming
codec2raw               mp2                     sox
crc                     mp3                     spdif
dash                    mp4                     spx
data                    mpeg1system             srt
daud                    mpeg1vcd                stream_segment
dfpwm                   mpeg1video              streamhash
dirac                   mpeg2dvd                sup
dnxhd                   mpeg2svcd               swf
dts                     mpeg2video              tee
dv                      mpeg2vob                tg2
eac3                    mpegts                  tgp
evc                     mpjpeg                  truehd
f4v                     mxf                     tta
ffmetadata              mxf_d10                 ttml
fifo                    mxf_opatom              uncodedframecrc
filmstrip               null                    vc1
fits                    nut                     vc1t
flac                    obu                     voc
flv                     oga                     vvc
framecrc                ogg                     w64
framehash               ogv                     wav
framemd5                oma                     webm
g722                    opus                    webm_chunk
g723_1                  pcm_alaw                webm_dash_manifest
g726                    pcm_f32be               webp
g726le                  pcm_f32le               webvtt
gif                     pcm_f64be               wsaud
gsm                     pcm_f64le               wtv
gxf                     pcm_mulaw               wv
h261                    pcm_s16be               yuv4mpegpipe

Enabled protocols:
async                   http                    rtmp
cache                   httpproxy               rtmpe
concat                  https                   rtmps
concatf                 icecast                 rtmpt
crypto                  ipfs_gateway            rtmpte
data                    ipns_gateway            rtmpts
fd                      libsrt                  rtp
ffrtmpcrypt             libssh                  srtp
ffrtmphttp              libzmq                  subfile
file                    md5                     tcp
ftp                     mmsh                    tee
gopher                  mmst                    tls
gophers                 pipe                    udp
hls                     prompeg                 udplite

Enabled filters:
a3dscope                datascope               pan
aap                     dblur                   perlin
abench                  dcshift                 perms
abitscope               dctdnoiz                perspective
acompressor             ddagrab                 phase
acontrast               deband                  photosensitivity
acopy                   deblock                 pixdesctest
acrossfade              decimate                pixelize
acrossover              deconvolve              pixscope
acrusher                dedot                   pp
acue                    deesser                 pp7
addroi                  deflate                 premultiply
adeclick                deflicker               prewitt
adeclip                 deinterlace_qsv         procamp_vaapi
adecorrelate            deinterlace_vaapi       pseudocolor
adelay                  dejudder                psnr
adenorm                 delogo                  pullup
aderivative             denoise_vaapi           qp
adrawgraph              deshake                 random
adrc                    despill                 readeia608
adynamicequalizer       detelecine              readvitc
adynamicsmooth          dialoguenhance          realtime
aecho                   dilation                remap
aemphasis               displace                removegrain
aeval                   doubleweave             removelogo
aevalsrc                drawbox                 repeatfields
aexciter                drawbox_vaapi           replaygain
afade                   drawgraph               reverse
afdelaysrc              drawgrid                rgbashift
afftdn                  drawtext                rgbtestsrc
afftfilt                drmeter                 roberts
afir                    dynaudnorm              rotate
afireqsrc               earwax                  rubberband
afirsrc                 ebur128                 sab
aformat                 edgedetect              scale
afreqshift              elbg                    scale2ref
afwtdn                  entropy                 scale_cuda
agate                   epx                     scale_qsv
agraphmonitor           eq                      scale_vaapi
ahistogram              equalizer               scdet
aiir                    erosion                 scharr
aintegral               estdif                  scroll
ainterleave             exposure                segment
alatency                extractplanes           select
alimiter                extrastereo             selectivecolor
allpass                 fade                    sendcmd
allrgb                  feedback                separatefields
allyuv                  fftdnoiz                setdar
aloop                   fftfilt                 setfield
alphaextract            field                   setparams
alphamerge              fieldhint               setpts
amerge                  fieldmatch              setrange
ametadata               fieldorder              setsar
amix                    fillborders             settb
amovie                  find_rect               sharpness_vaapi
amplify                 firequalizer            shear
amultiply               flanger                 showcqt
anequalizer             floodfill               showcwt
anlmdn                  format                  showfreqs
anlmf                   fps                     showinfo
anlms                   framepack               showpalette
anoisesrc               framerate               showspatial
anull                   framestep               showspectrum
anullsink               freezedetect            showspectrumpic
anullsrc                freezeframes            showvolume
apad                    fspp                    showwaves
aperms                  fsync                   showwavespic
aphasemeter             gblur                   shuffleframes
aphaser                 geq                     shufflepixels
aphaseshift             gradfun                 shuffleplanes
apsnr                   gradients               sidechaincompress
apsyclip                graphmonitor            sidechaingate
apulsator               grayworld               sidedata
arealtime               greyedge                sierpinski
aresample               guided                  signalstats
areverse                haas                    signature
arls                    haldclut                silencedetect
arnndn                  haldclutsrc             silenceremove
asdr                    hdcd                    sinc
asegment                headphone               sine
aselect                 hflip                   siti
asendcmd                highpass                smartblur
asetnsamples            highshelf               smptebars
asetpts                 hilbert                 smptehdbars
asetrate                histeq                  sobel
asettb                  histogram               spectrumsynth
ashowinfo               hqdn3d                  speechnorm
asidedata               hqx                     split
asisdr                  hstack                  spp
asoftclip               hstack_qsv              sr_amf
aspectralstats          hstack_vaapi            ssim
asplit                  hsvhold                 ssim360
ass                     hsvkey                  stereo3d
astats                  hue                     stereotools
astreamselect           huesaturation           stereowiden
asubboost               hwdownload              streamselect
asubcut                 hwmap                   subtitles
asupercut               hwupload                super2xsai
asuperpass              hwupload_cuda           superequalizer
asuperstop              hysteresis              surround
atadenoise              identity                swaprect
atempo                  idet                    swapuv
atilt                   il                      tblend
atrim                   inflate                 telecine
avectorscope            interlace               testsrc
avgblur                 interleave              testsrc2
avsynctest              join                    thistogram
axcorrelate             kerndeint               threshold
azmq                    kirsch                  thumbnail
backgroundkey           lagfun                  thumbnail_cuda
bandpass                latency                 tile
bandreject              lenscorrection          tiltandshift
bass                    libvmaf                 tiltshelf
bbox                    life                    tinterlace
bench                   limitdiff               tlut2
bilateral               limiter                 tmedian
bilateral_cuda          loop                    tmidequalizer
biquad                  loudnorm                tmix
bitplanenoise           lowpass                 tonemap
blackdetect             lowshelf                tonemap_vaapi
blackframe              lumakey                 tpad
blend                   lut                     transpose
blockdetect             lut1d                   transpose_vaapi
blurdetect              lut2                    treble
bm3d                    lut3d                   tremolo
boxblur                 lutrgb                  trim
bwdif                   lutyuv                  unpremultiply
bwdif_cuda              mandelbrot              unsharp
cas                     maskedclamp             untile
ccrepack                maskedmax               uspp
cellauto                maskedmerge             v360
channelmap              maskedmin               vaguedenoiser
channelsplit            maskedthreshold         varblur
chorus                  maskfun                 vectorscope
chromahold              mcdeint                 vflip
chromakey               mcompand                vfrdet
chromakey_cuda          median                  vibrance
chromanr                mergeplanes             vibrato
chromashift             mestimate               vidstabdetect
ciescope                metadata                vidstabtransform
codecview               midequalizer            vif
color                   minterpolate            vignette
colorbalance            mix                     virtualbass
colorchannelmixer       monochrome              vmafmotion
colorchart              morpho                  volume
colorcontrast           movie                   volumedetect
colorcorrect            mpdecimate              vpp_amf
colorhold               mptestsrc               vpp_qsv
colorize                msad                    vstack
colorkey                multiply                vstack_qsv
colorlevels             negate                  vstack_vaapi
colormap                nlmeans                 w3fdif
colormatrix             nnedi                   waveform
colorspace              noformat                weave
colorspace_cuda         noise                   xbr
colorspectrum           normalize               xcorrelate
colortemperature        null                    xfade
compand                 nullsink                xmedian
compensationdelay       nullsrc                 xpsnr
concat                  oscilloscope            xstack
convolution             overlay                 xstack_qsv
convolve                overlay_cuda            xstack_vaapi
copy                    overlay_qsv             yadif
corr                    overlay_vaapi           yadif_cuda
cover_rect              owdenoise               yaepblur
crop                    pad                     yuvtestsrc
cropdetect              pad_vaapi               zmq
crossfeed               pal100bars              zoneplate
crystalizer             pal75bars               zoompan
cue                     palettegen              zscale
curves                  paletteuse

Enabled bsfs:
aac_adtstoasc           h264_mp4toannexb        pcm_rechunk
av1_frame_merge         h264_redundant_pps      pgs_frame_merge
av1_frame_split         hapqa_extract           prores_metadata
av1_metadata            hevc_metadata           remove_extradata
chomp                   hevc_mp4toannexb        setts
dca_core                imx_dump_header         showinfo
dovi_rpu                media100_to_mjpegb      text2movsub
dts2pts                 mjpeg2jpeg              trace_headers
dump_extradata          mjpega_dump_header      truehd_core
dv_error_marker         mov2textsub             vp9_metadata
eac3_core               mpeg2_metadata          vp9_raw_reorder
evc_frame_merge         mpeg4_unpack_bframes    vp9_superframe
extract_extradata       noise                   vp9_superframe_split
filter_units            null                    vvc_metadata
h264_metadata           opus_metadata           vvc_mp4toannexb

Enabled indevs:
dshow                   lavfi
gdigrab                 vfwcap

Enabled outdevs:

git-essentials external libraries' versions: 

AMF v1.4.36.0
aom v3.12.0-44-g4e3595a426
AviSynthPlus v3.7.4
ffnvcodec n13.0.19.0-1-gf2fb9b3
freetype VER-2-13-3
fribidi v1.0.16-2-gb28f43b
gsm 1.0.22
harfbuzz 11.0.0-87-g4954edb2
lame 3.100
libass 0.17.3-80-g958f4b6
libgme 0.6.3
libopencore-amrnb 0.1.6
libopencore-amrwb 0.1.6
libssh 0.11.1
libtheora 1.1.1
libwebp v1.5.0-17-ga4183d94
oneVPL 2.14
openmpt libopenmpt-0.6.22-23-gdbcfe978c
opus v1.5.2-95-gdf02d25f
rubberband v1.8.1
SDL release-2.32.0-30-g2e4c12cd2
speex Speex-1.2.1-45-g4e231b4
srt v1.5.4-31-g952f949
VAAPI 2.23.0.
vidstab v1.1.1-14-gd2d55a8
vmaf v3.0.0-108-g8b2582db
vo-amrwbenc 0.1.3
vorbis v1.3.7-10-g84c02369
vpx v1.15.0-70-gd1186e5b1
x264 v0.165.3214
x265 4.1-126-gb354c009a
xvid v1.3.7
zeromq 4.3.5
zimg release-3.0.5-201-g33b2b71

