# meme_maker_pro_2003_btw

## build docker

```bash
docker build -t meme-maker .
```

## run docker

```bash
docker run -v $(pwd)/meme_maker_pro_2003_btw:/app/meme_maker_pro_2003_btw -p 3228:3228 -it meme-maker
```
